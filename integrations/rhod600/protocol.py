"""Genesis Rhod 600: verified six-zone, seven-color HID lighting protocol.

Pure helpers: safe to unit-test without hardware.
Seven fixed colors were recovered from actual ShinetekTools outbound reports.
"""
from __future__ import annotations

NAMES = ("OFF", "RED", "GREEN", "BLUE", "YELLOW", "CYAN", "MAGENTA", "WHITE")
COLORS = {name: i for i, name in enumerate(NAMES)}
PREFIX = (0x07, 0xFF, 0x70)
SUFFIX = (0x03, 0x00)
AREA_COUNT = 6
SUPPORTED_EVENTS = ("ALERT", "ERROR", "SUCCESS", "NOTICE", "ACK", "STOP")
EVENT_COLORS = {
    "ERROR": (COLORS["RED"], COLORS["YELLOW"]),
    "ALERT": (COLORS["RED"], COLORS["BLUE"]),
    "SUCCESS": (COLORS["GREEN"], COLORS["WHITE"]),
    "NOTICE": (COLORS["GREEN"], COLORS["YELLOW"]),
}
IDLE = tuple(COLORS[s] for s in ("MAGENTA", "YELLOW", "CYAN", "GREEN", "BLUE", "WHITE"))


def report_for_areas(areas: tuple[int, ...] | list[int]) -> bytes:
    if len(areas) != AREA_COUNT or any(type(x) is not int or not 0 <= x <= 7 for x in areas):
        raise ValueError("Exactly six color indices in the range 0..7 are required")
    return bytes((*PREFIX,
        (areas[0] << 4) | areas[1],
        (areas[2] << 4) | areas[3],
        (areas[4] << 4) | areas[5], *SUFFIX))


def decode_lighting_report(report: bytes) -> tuple[int, ...]:
    if len(report) != 8 or tuple(report[:3]) != PREFIX or tuple(report[6:]) != SUFFIX:
        raise ValueError("Not a verified Rhod 600 FF70 color report")
    return tuple(v for packed in report[3:6] for v in (packed >> 4, packed & 15))


def event_areas(event: str, phase: int) -> tuple[int, ...]:
    if event not in EVENT_COLORS:
        raise ValueError("Unknown RGB event")
    a, b = EVENT_COLORS[event]
    return tuple((a if (zone + phase) % 2 == 0 else b) for zone in range(AREA_COUNT))


def idle_areas(step: int) -> tuple[int, ...]:
    return tuple(IDLE[(i + step) % AREA_COUNT] for i in range(AREA_COUNT))


def round_robin_index(tick: int, events: int) -> int:
    return 0 if events == 0 else (tick // 4) % events
