"""Genesis Rhod 600 six-zone lighting daemon, opt-in and local only.

UDP protocol at 127.0.0.1:45894: RHOD600:ERROR/ALERT/SUCCESS/NOTICE/ACK.
Reuses the same event categories as the P93 bridge.
"""
from __future__ import annotations
import argparse
import ctypes
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import signal
import socket
import sys
import time

from protocol import (
    AREA_COUNT, COLORS, SUPPORTED_EVENTS, event_areas, idle_areas,
    report_for_areas, round_robin_index,
)
from hid import RhodDeviceError, discover, set_colors, vendor_software_running

PORT=45894
BASE=Path(os.environ.get("RHOD600_STATE_DIR",
     str(Path.home()/"Portable"/"Automation"/"Rhod600-Signals")))
STATE_FILE=BASE/"state.json"
LOG_FILE=BASE/"bridge.log"
VALID_PENDING={"ERROR","ALERT","SUCCESS","NOTICE"}
CAPACITY=16
ALERT_INTERVAL=0.95
IDLE_INTERVAL=1.25


def logger():
    BASE.mkdir(parents=True, exist_ok=True)
    log=logging.getLogger("rhod600-signals")
    log.setLevel(logging.INFO)
    if not log.handlers:
        h=RotatingFileHandler(LOG_FILE,maxBytes=180_000,backupCount=2,encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(h)
    return log


def load_pending()->list[str]:
    try:
        stored=json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(stored,dict):
            return []
        return [x for x in stored.get("pending",[]) if isinstance(x,str) and x in VALID_PENDING][-CAPACITY:]
    except (OSError,ValueError,TypeError):
        return []


def store_pending(events:list[str])->None:
    BASE.mkdir(parents=True,exist_ok=True)
    temp=STATE_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps({"pending":events},ensure_ascii=False)+"\n",encoding="utf-8")
    os.replace(temp,STATE_FILE)


def process_event(events:list[str], kind:str)->list[str]:
    if kind in VALID_PENDING:
        return (events+[kind])[-CAPACITY:]
    if kind in {"ACK","STOP"}:
        return []
    return events


def run_daemon(enable_hardware:bool, duration:int|None=None)->int:
    if not enable_hardware:
        raise ValueError("Starting the RGB daemon requires explicit --enable-hardware")
    targets=discover()
    if len(targets)!=1:
        raise RhodDeviceError(f"Expected 1 verified Rhod600 HID target, found {len(targets)}")
    if vendor_software_running():
        raise RhodDeviceError("Close ShinetekTools.exe before starting Rhod RGB service")

    log=logger()
    events=load_pending()
    socket_in=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    socket_in.bind(("127.0.0.1",PORT))
    socket_in.settimeout(0.25)
    log.info("Rhod600 service started, pending_categories=%d",len(events))
    tick=0
    idle_step=0
    next_at=time.monotonic()
    start=time.monotonic()
    last_error_at=0.0
    running=True
    def stop(*_args):
        nonlocal running
        running=False
    if hasattr(signal,"SIGINT"):
        signal.signal(signal.SIGINT,stop)
    if hasattr(signal,"SIGTERM"):
        signal.signal(signal.SIGTERM,stop)
    try:
        while running and (duration is None or time.monotonic()-start < duration):
            try:
                msg,addr=socket_in.recvfrom(64)
                if addr[0]!="127.0.0.1":
                    continue
                if not msg.startswith(b"RHOD600:"):
                    continue
                try: kind=msg[8:].decode("ascii")
                except UnicodeDecodeError: continue
                if kind not in SUPPORTED_EVENTS:continue
                events=process_event(events,kind)
                store_pending(events)
                log.info("event=%s pending=%d",kind,len(events))
                tick=0
                next_at=0
            except socket.timeout:
                pass
            if time.monotonic()<next_at:
                continue
            if events:
                index=round_robin_index(tick,len(events))
                areas=event_areas(events[index],tick%2)
                tick+=1
                interval=ALERT_INTERVAL
            else:
                areas=idle_areas(idle_step)
                idle_step+=1
                interval=IDLE_INTERVAL
            try:
                set_colors(areas,enabled=enable_hardware)
                next_at=time.monotonic()+interval
            except RhodDeviceError as exc:
                now=time.monotonic()
                if now-last_error_at>10:
                    log.warning("Rhod600 lighting paused: %s",str(exc))
                    last_error_at=now
                next_at=now+4
    finally:
        socket_in.close()
        log.info("Rhod600 service stopped")
    return 0


def send_event(event:str)->None:
    if event not in SUPPORTED_EVENTS:
        raise ValueError("Unsupported event")
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.sendto(f"RHOD600:{event}".encode("ascii"),("127.0.0.1",PORT))


def main()->int:
    ap=argparse.ArgumentParser(description="Genesis Rhod 600 fixed-seven-color keyboard notification adapter")
    ap.add_argument("--probe",action="store_true",help="List matching device capabilities; no writes")
    ap.add_argument("--dry-run",action="store_true",help="Print test packets and exit; no writes")
    ap.add_argument("--serve",action="store_true",help="Run local event receiver")
    ap.add_argument("--enable-hardware",action="store_true",help="Explicitly permit verified HID RGB writes")
    ap.add_argument("--one-shot",metavar="COLOR0,...,COLOR5",
                    help="Six 0..7 color indices; one feature report, no persistence")
    ap.add_argument("--event",choices=SUPPORTED_EVENTS,help="Send one event to running daemon")
    ap.add_argument("--duration",type=int,help="Stop daemon after N seconds (hardware tests)")
    args=ap.parse_args()
    if args.probe:
        found=discover()
        print("MATCHING_VERIFIED_RHOD600_DEVICES="+str(len(found)))
        for _,caps in found: print("CAPABILITIES="+str(caps))
        print("VENDOR_APPLICATION_RUNNING="+str(vendor_software_running()))
        return 0 if len(found)==1 else 2
    if args.dry_run:
        for kind in ("ERROR","ALERT","SUCCESS","NOTICE"):
            for phase in range(2):
                print(kind,phase,report_for_areas(event_areas(kind,phase)).hex(" "))
        print("IDLE",report_for_areas(idle_areas(0)).hex(" "))
        return 0
    if args.event:
        send_event(args.event)
        print("LOCAL_SIGNAL_SENT="+args.event)
        return 0
    if args.one_shot is not None:
        nums=[int(n.strip()) for n in args.one_shot.split(",")]
        report=report_for_areas(nums)
        if not args.enable_hardware:
            print("DRY_RUN_REPORT="+report.hex(" "))
            print("Pass --enable-hardware for a single verified 8-byte HID write")
            return 0
        set_colors(nums,enabled=True)
        print("VERIFIED_LIGHTING_REPORT_SENT="+report.hex(" "))
        return 0
    if args.serve:
        return run_daemon(args.enable_hardware,args.duration)
    ap.print_help()
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (OSError,RhodDeviceError,ValueError) as e:
        print("ERROR:",str(e),file=sys.stderr)
        sys.exit(1)
