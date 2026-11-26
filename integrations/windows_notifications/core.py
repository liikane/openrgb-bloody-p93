"""Offline notification policy and opt-in P93 transport; no Windows listener."""
from dataclasses import dataclass
from enum import Enum
import socket
import threading


class EventKind(str, Enum):
    ALERT = "ALERT"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"
    NOTICE = "NOTICE"


@dataclass(frozen=True)
class NotificationEvent:
    """Version 1 shared event schema: a classification only, never Toast content."""
    kind: EventKind

    def __post_init__(self):
        if not isinstance(self.kind, EventKind):
            raise ValueError("kind must be an EventKind")


@dataclass(frozen=True)
class ToastId:
    app_id: str
    notification_id: int

    def __post_init__(self):
        if not isinstance(self.app_id, str) or not self.app_id.strip():
            raise ValueError("app_id must be a non-empty string")
        if (type(self.notification_id) is not int
                or not 0 <= self.notification_id <= 0xFFFFFFFF):
            raise ValueError("notification_id must be an unsigned 32-bit integer")


class NotificationPolicy:
    """Reconcile complete snapshots; retain seen IDs for this process session."""
    MAX_SEEN = 100_000

    def __init__(self):
        self._rules = {}
        self._seen = set()
        self._initialized = False
        self._lock = threading.Lock()

    def set_rules(self, rules):
        """Replace the allowlist with app ID -> EventKind rules."""
        validated = dict(rules)
        for app_id, kind in validated.items():
            if not isinstance(app_id, str) or not app_id.strip() or not isinstance(kind, EventKind):
                raise ValueError("rules must map non-empty app IDs to EventKind values")
        with self._lock:
            self._rules = validated

    def _snapshot(self, notifications):
        snapshot = set()
        for notification in notifications:
            if not isinstance(notification, ToastId):
                raise ValueError("snapshots must contain only ToastId values")
            snapshot.add(notification)
            if len(snapshot) > self.MAX_SEEN:
                raise ValueError("notification snapshot exceeds the session limit")
        return snapshot

    def initialize(self, notifications):
        """Seed the startup baseline without producing events."""
        snapshot = self._snapshot(notifications)
        with self._lock:
            if self._initialized:
                raise RuntimeError("notification policy is already initialized")
            self._seen = snapshot
            self._initialized = True

    def process_snapshot(self, notifications):
        """Return events for previously unseen, allowlisted notification IDs."""
        snapshot = self._snapshot(notifications)
        with self._lock:
            if not self._initialized:
                raise RuntimeError("initialize with a startup snapshot first")
            new = snapshot - self._seen
            if len(self._seen) + len(new) > self.MAX_SEEN:
                raise RuntimeError("notification session limit reached; restart with a fresh baseline")
            self._seen.update(new)
            return [NotificationEvent(self._rules[item.app_id])
                    for item in sorted(new, key=lambda item: (item.app_id, item.notification_id))
                    if item.app_id in self._rules]


class P93Sender:
    """Send only event codes to the fixed P93 loopback endpoint after opt-in."""
    def __init__(self):
        self._enabled = False
        self._lock = threading.Lock()

    def set_enabled(self, enabled):
        if type(enabled) is not bool:
            raise ValueError("enabled must be a boolean")
        with self._lock:
            self._enabled = enabled

    def send(self, event):
        if not isinstance(event, NotificationEvent):
            raise ValueError("event must be a NotificationEvent")
        with self._lock:
            if not self._enabled:
                return False
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(("P93:" + event.kind.value).encode("ascii"), ("127.0.0.1", 45893))
            return True
