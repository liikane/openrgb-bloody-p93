# Bloody P93 — documented RGB HID commands

This document records a **community-derived, experimentally verified** subset of the HID protocol. It is not manufacturer documentation. The procedure was tested on a real Bloody P93 (USB `09DA:31DE`, HID `MI_02/COL04`).

## Device identity and transport

| Field | Value |
| --- | --- |
| USB VID/PID | `0x09DA / 0x31DE` |
| HID collection | `MI_02/COL04` |
| Usage page / usage | `0xFF32 / 0x0218` |
| Feature report length | 64 bytes |
| Report ID | `0x07` |
| Transport | Windows HID `HidD_SetFeature`, no custom driver |
| Read-only identity verification | Windows `HidD_GetFeature`: starts with `07 03 06` |

**Only verified RGB report types are supported.** Do not send untested report values to the mouse: other vendor-specific commands may change stored profiles or firmware.

## Feature report layout (64 bytes)

| Byte offset | Value | Meaning |
| --- | --- | --- |
| 0 | `07` | HID Report ID |
| 1 | `03` | Vendor command family |
| 2 | `06` | Vendor command family |
| 3 | `01`, `00`, or `02` | RGB initialization / direct mode / RGB colors |
| 4–7 | `00` | Reserved in tested commands |
| 8–52 | Fifteen RGB triplets | For `07 03 06 02`: 15 x (R,G,B), beginning at byte 8 |
| 53–63 | `00` | Reserved/unused in tested commands |

### Command A — enter RGB control mode

`07 03 06 01 00 00 00 00 00 ... 00` (64 bytes).

### Command B — enable Direct RGB operation

`07 03 06 00 00 00 00 00 01 00 ... 00` (64 bytes).

### Command C — set RGB colors

`07 03 06 02 00 00 00 00 [R1 G1 B1] ... [R15 G15 B15] 00 ... 00` (64 bytes).

Examples:

- Purple all slots: R=160, G=0, B=255 = `#A000FF`.
- Yellow all slots: `#FFD200`.
- Solid red: `#FF0000`.
- All off: `#000000`.
- Beacon effect: send an array with group A slots yellow / group B off, then alternate; delays are software-controlled.

The byte-level layout is verified by reading back the HID report and successfully changing a real P93 mouse to static purple and performing red/green flashing. **The mapping from each of the 15 HID color slots to physical mouse LEDs is not yet fully documented.** The fact that a mouse supports animated effects does not by itself establish whether every physical LED corresponds to a unique report slot.

## Sequence and examples

Use `RgbMode()` and `DirectInit()` once when opening a device, then `ColorSlots()` for each frame. The implementation is in [P93Protocol.h](../src/P93Protocol.h) and [P93Hid.cpp](../src/P93Hid.cpp).

### Changing individual color slots

The OpenRGB Devices screen presents 15 labelled **HID slot 1–15** entries in the experimental v0.2 plugin. Select a slot and choose a color, or use **Identify next LED slot** to illuminate one slot at a time and record which physical region responds.

### Beacon animation

The plug-in alternates colors in two user-selectable **slot groups A and B** (default slots 1–7 versus 8–15). Users should identify the real physical mapping before treating groups as “left” and “right”.

Interval is adjustable from 120 to 2000 milliseconds. The animation uses known RGB color reports only; it does not change mouse button profiles.

## Local notification protocol

The plugin can optionally listen on loopback UDP **127.0.0.1:45893**. The listener is **disabled by default** and only starts when both **Enable RGB control** and **Enable local notification commands** are checked.

One ASCII datagram per event (no authentication; local machine only):

| Datagram | Result |
| --- | --- |
| `P93:ALERT` | 5 seconds of alternating yellow groups |
| `P93:NOTICE` | 5 seconds of alternating yellow groups |
| `P93:ERROR` | 5 seconds of alternating red groups |
| `P93:SUCCESS` | 1.8 seconds of solid green |
| `P93:STOP` | Stop animation, restore the current OpenRGB color selection |

PowerShell usage from the repo:

```powershell
.\Send-P93Notification.ps1 -Event ALERT
.\Send-P93Notification.ps1 -Event SUCCESS
```

A local program, scheduled task, or ntfy client can invoke this script upon a relevant event. The plugin does **not** log keystrokes, contact any cloud service, or automatically subscribe to an ntfy server.

## Safety and limitations

- Feature reports are **RGB-only**; this software never invokes profile-writing, macro reassignment, firmware update or bootloader commands.
- The earlier physical test confirmed visible RGB changes and continued mouse-button operation.
- The 15-slot map, effect timing and notification integration require additional physical verification in the v0.2 build.
- Opening Bloody WorkShop 8 concurrently may overwrite RGB colors; close its lighting editor during tests, without changing existing button mappings.
- Send untrusted data only after explicit local notification enablement; local UDP listener intentionally has no network exposure beyond loopback.
- This is an independently derived community protocol, **not a manufacturer-supported API**.
