#!/usr/bin/env python3
"""True Mouse Art: ntfy + selected Windows Event Log events -> local OpenRGB RGB.

Standard library only. No notification bodies are stored or forwarded.
Windows Event Log is NOT the Windows Toast notification center.
"""
from __future__ import annotations

import argparse
import collections
import ctypes
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import queue
import re
import signal
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = Path(__file__).resolve().parent
DEFAULT_SETTINGS = Path.home() / "Portable" / "Automation" / "Summary" / "settings.json"
STATE_DIR = Path(os.environ.get("P93_BRIDGE_STATE_DIR", str(Path.home() / "Portable" / "Automation" / "OpenRGB-Ntfy-Bridge")))
LOG_PATH = STATE_DIR / "bridge.log"
LOCAL_IP = "127.0.0.1"
LOCAL_PORT = 45893

# Windows Event Logs: receive future matched events only, not private event descriptions.
SYSTEM_EVENTS = (
    ("Microsoft-Windows-Windows Defender/Operational", 1116, "ERROR"),
    ("Microsoft-Windows-Windows Defender/Operational", 1117, "ALERT"),
    ("Microsoft-Windows-WindowsUpdateClient/Operational", 19, "SUCCESS"),
    ("Microsoft-Windows-WindowsUpdateClient/Operational", 20, "ERROR"),
)
VALID_EVENTS = {"ALERT", "NOTICE", "ERROR", "SUCCESS", "STOP"}


def setup_logger() -> logging.Logger:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("true-mouse-art-bridge")
    log.setLevel(logging.INFO)
    if not log.handlers:
        h = RotatingFileHandler(LOG_PATH, maxBytes=150_000, backupCount=2, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(h)
    return log


def load_ntfy_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8-sig"))
    server = str(cfg.get("ntfy_server", "")).rstrip("/")
    topic = str(cfg.get("ntfy_topic", ""))
    parsed = urllib.parse.urlparse(server)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("ntfy_server must be a normal HTTPS URL")
    if not re.fullmatch(r"[A-Za-z0-9_-]{12,}", topic):
        raise ValueError("Invalid ntfy topic")
    return {"server": server, "topic": topic, "token": str(cfg.get("ntfy_token") or "")}


def classify_ntfy(msg: dict) -> str | None:
    """Recognize explicit event types before trying title/tags; ignore message body."""
    if msg.get("event") != "message":
        return None
    tags = {str(t).lower() for t in msg.get("tags", []) if isinstance(t, str)}
    title = str(msg.get("title", "")).lower()[:150]
    # Explicit tags: senders can use one of these instead of text classification.
    if tags & {"p93_error", "error", "x", "rotating_light", "no_entry"}:
        return "ERROR"
    if tags & {"p93_success", "success", "white_check_mark", "heavy_check_mark", "tada"}:
        return "SUCCESS"
    if tags & {"p93_alert", "warning", "sos", "exclamation", "bell"}:
        return "ALERT"
    if re.search(r"\b(error|failed|failure|viga|ebaõnnest|nurjus)\b", title):
        return "ERROR"
    if re.search(r"\b(success|completed|finished|ready|done|valmis|tehtud|õnnestus)\b", title):
        return "SUCCESS"
    try:
        priority = int(msg.get("priority", 3))
    except (TypeError, ValueError):
        priority = 3
    if priority >= 4:
        return "ALERT"
    if priority <= 2:
        return None
    return "NOTICE"


class WindowsEventSource:
    """Native Windows push subscriptions: no polling, no event body retrieval."""
    def __init__(self, outgoing: queue.Queue, log: logging.Logger):
        self.outgoing = outgoing
        self.log = log
        self.handles = []
        self.callbacks = []
        self.dll = None

    def start(self) -> int:
        if os.name != "nt":
            self.log.info("Windows Event Log integration unavailable on this platform")
            return 0
        from ctypes import wintypes
        dll = ctypes.WinDLL("wevtapi", use_last_error=True)
        cb_type = ctypes.WINFUNCTYPE(wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p)
        dll.EvtSubscribe.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.LPCWSTR,
                                     wintypes.LPCWSTR, ctypes.c_void_p, ctypes.c_void_p, cb_type, wintypes.DWORD]
        dll.EvtSubscribe.restype = ctypes.c_void_p
        dll.EvtClose.argtypes = [ctypes.c_void_p]
        dll.EvtClose.restype = wintypes.BOOL
        self.dll = dll

        for channel, event_id, kind in SYSTEM_EVENTS:
            def callback(action, unused_context, event_handle, src=channel, eid=event_id, event=kind):
                try:
                    if action == 1:  # EvtSubscribeActionDeliver
                        self.outgoing.put_nowait((event, f"Windows EventLog {eid}"))
                    elif action == 0:
                        self.log.warning("Windows event subscription callback error channel=%s id=%s", src, eid)
                except queue.Full:
                    self.log.warning("Event buffer full, dropping Windows event")
                except Exception:
                    self.log.exception("Windows event callback failed")
                return 0
            cb = cb_type(callback)
            self.callbacks.append(cb)  # keep callback alive while native subscription is active
            query = f"*[System[(EventID={event_id})]]"
            handle = dll.EvtSubscribe(None, None, channel, query, None, None, cb, 1)
            if not handle:
                self.log.warning("Windows subscription unavailable for event %d (Win32 error %d)",
                                 event_id, ctypes.get_last_error())
                continue
            self.handles.append(handle)
            self.log.info("Windows event subscriber active: event_id=%d", event_id)
        return len(self.handles)

    def close(self):
        if self.dll:
            for handle in self.handles:
                self.dll.EvtClose(handle)
        self.handles.clear()
        self.callbacks.clear()


class NtfySource:
    def __init__(self, cfg: dict, outgoing: queue.Queue, shutdown: threading.Event, log: logging.Logger):
        self.cfg = cfg
        self.outgoing = outgoing
        self.shutdown = shutdown
        self.log = log
        self.seen = collections.deque(maxlen=400)
        self.seen_set = set()
        self.since = str(int(time.time()))
        self.seen_lock = threading.Lock()

    def _remember(self, message_id: str, timestamp: int | None = None):
        with self.seen_lock:
            if not message_id or message_id in self.seen_set:
                return False
            if len(self.seen) >= self.seen.maxlen:
                self.seen_set.discard(self.seen.popleft())
            self.seen.append(message_id)
            self.seen_set.add(message_id)
            if timestamp is not None:
                # Cache replay by timestamp is more resilient than by message ID.
                self.since = str(max(int(self.since), timestamp))
            return True

    def handle_message(self, message: dict, source: str):
        if message.get("event") != "message":
            return
        stamp = message.get("time")
        if not isinstance(stamp, (int, float)):
            return
        stamp = int(stamp)
        msg_id = str(message.get("id", ""))
        if not self._remember(msg_id, stamp):
            return
        # Do not flash on messages that have been cached for several minutes.
        if stamp < int(time.time()) - 120:
            return
        event = classify_ntfy(message)
        if event:
            try:
                self.outgoing.put_nowait((event, source))
            except queue.Full:
                self.log.warning("Event buffer full, dropping ntfy event")

    def poll_loop(self):
        """Fallback for long-lived streams that silently stop delivering messages."""
        url = self.cfg["server"] + "/" + self.cfg["topic"] + "/json"
        while not self.shutdown.wait(12):
            with self.seen_lock:
                since = self.since
            req_url = url + "?poll=1&since=" + urllib.parse.quote(since, safe="")
            headers = {"Accept": "application/x-ndjson", "User-Agent": "TrueMouseArt-ntfy-bridge/0.2"}
            if self.cfg["token"]:
                headers["Authorization"] = "Bearer " + self.cfg["token"]
            try:
                with urllib.request.urlopen(urllib.request.Request(req_url, headers=headers), timeout=15) as response:
                    # Read only up to 256 KiB per poll to limit memory on a busy shared topic.
                    body = response.read(262_145)
                    if len(body) > 262_144:
                        self.log.warning("ntfy poll response too large; skipped")
                        continue
                for raw in body.splitlines():
                    try:
                        message = json.loads(raw)
                    except (ValueError, UnicodeError):
                        continue
                    self.handle_message(message, "ntfy-poll")
            except Exception as ex:
                # Keep any exception text (which may contain a private URL) out of logs.
                self.log.warning("ntfy fallback poll failed (%s)", type(ex).__name__)

    def run(self):
        url = self.cfg["server"] + "/" + self.cfg["topic"] + "/json"
        delay = 2
        while not self.shutdown.is_set():
            req_url = url + "?since=" + urllib.parse.quote(self.since, safe="")
            headers = {"Accept": "application/x-ndjson", "User-Agent": "TrueMouseArt-ntfy-bridge/0.1"}
            if self.cfg["token"]:
                headers["Authorization"] = "Bearer " + self.cfg["token"]
            try:
                with urllib.request.urlopen(urllib.request.Request(req_url, headers=headers), timeout=45) as response:
                    self.log.info("Connected to ntfy HTTPS JSON stream")
                    delay = 2
                    for raw in response:
                        if self.shutdown.is_set():
                            return
                        if len(raw) > 32_000:
                            self.log.warning("ntfy event too large; skipped")
                            continue
                        try:
                            message = json.loads(raw)
                        except (ValueError, UnicodeError):
                            continue
                        self.handle_message(message, "ntfy-stream")
            except (TimeoutError, OSError, urllib.error.URLError, urllib.error.HTTPError) as ex:
                # Do not log exception text: it may include the private URL/topic.
                code = getattr(ex, "code", None)
                self.log.warning("ntfy connection interrupted (%s%s)",
                                 type(ex).__name__, f", HTTP {code}" if code else "")
            except Exception as ex:
                self.log.warning("ntfy parser disconnected (%s)", type(ex).__name__)
            self.shutdown.wait(delay)
            delay = min(delay * 2, 45)


def send_local(event: str) -> None:
    if event not in VALID_EVENTS:
        raise ValueError("Invalid local event")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.sendto(f"P93:{event}".encode("ascii"), (LOCAL_IP, LOCAL_PORT))


def run_bridge(config_path: Path, windows_events: bool, ntfy_events: bool,
               check_only: bool = False, self_test: str | None = None) -> int:
    log = setup_logger()
    cfg = load_ntfy_config(config_path) if ntfy_events else None
    q: queue.Queue = queue.Queue(maxsize=256)
    shutdown = threading.Event()
    watcher = WindowsEventSource(q, log)
    count = watcher.start() if windows_events else 0
    if windows_events and count == 0:
        log.warning("Windows Event Log subscriptions could not be enabled")

    if check_only:
        print(f"NTFY_CONFIG={'OK' if cfg else 'DISABLED'}")
        print(f"WINDOWS_EVENT_SUBSCRIPTIONS={count}")
        print(f"CONFIG_CONTENTS_NOT_PRINTED=true")
        watcher.close()
        return 0 if (not windows_events or count > 0) else 2

    if self_test:
        send_local(self_test)
        print(f"LOCAL_TEST_SENT={self_test}")
        watcher.close()
        return 0

    def stop(*_args):
        shutdown.set()

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
    worker = None
    if cfg:
        source = NtfySource(cfg, q, shutdown, log)
        worker = threading.Thread(target=source.run, daemon=True, name="ntfy-stream")
        worker.start()
        poll_worker = threading.Thread(target=source.poll_loop, daemon=True, name="ntfy-poll")
        poll_worker.start()
    log.info("Bridge started ntfy=%s windows_subscribers=%d", bool(cfg), count)
    try:
        while not shutdown.is_set():
            try:
                event, source = q.get(timeout=1.0)
            except queue.Empty:
                continue
            # No titles, messages or private event payloads in logs.
            try:
                send_local(event)
                log.info("Sent local P93 event=%s source=%s", event, source)
            except OSError as ex:
                log.warning("Local UDP send failed %s", type(ex).__name__)
    finally:
        watcher.close()
        log.info("Bridge stopped")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bridge ntfy and selected Windows EventLog events to OpenRGB P93.")
    parser.add_argument("--settings", type=Path,
                        default=Path(os.environ.get("NTFY_BRIDGE_SETTINGS", str(DEFAULT_SETTINGS))))
    parser.add_argument("--no-ntfy", action="store_true")
    parser.add_argument("--no-windows-events", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--test", choices=sorted(VALID_EVENTS), help="Send one local P93 event, then exit")
    args = parser.parse_args()
    instance_handle = None
    if os.name == "nt" and not args.check and not args.test:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        kernel.CreateMutexW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        instance_handle = kernel.CreateMutexW(None, 1, r"Local\TrueMouseArtNotificationBridge")
        if not instance_handle:
            print("ERROR: cannot create singleton lock", file=sys.stderr)
            sys.exit(1)
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
            kernel.CloseHandle(instance_handle)
            sys.exit(0)
    try:
        sys.exit(run_bridge(args.settings, not args.no_windows_events, not args.no_ntfy,
                            args.check, args.test))
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
    finally:
        if instance_handle:
            kernel.CloseHandle(instance_handle)
