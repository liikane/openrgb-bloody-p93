# Hardware and integration validation — v0.2.1

**Date:** 2026-11-10  
**Host:** LAURIDELL (Windows)  
**OpenRGB:** 1.1 x64 portable  
**Mouse:** Bloody P93, USB `09DA:31DE`, HID `MI_02/COL04`  
**Scope:** real-device HID report tests; not a camera/visual mapping test.

## Automated build
- GitHub Actions [run 42780902835](https://github.com/liikane/openrgb-bloody-p93/actions/runs/42780902835) — **success**.
- MSVC 2022 + Qt 6.8.3 plugin build and unit tests of 64-byte HID report layout — **passed**.
- v0.2.0 was blocked at runtime due to missing `Qt6Network.dll` in the OpenRGB portable distribution. v0.2.1 replaces the QtNetwork UDP dependency with Windows Winsock2.

## Local installation and loading
- v0.2.1 DLL installed to `%APPDATA%\OpenRGB\plugins\OpenRGBBloodyP93Plugin.dll`.
- OpenRGB application log confirms `Registering RGB controller Bloody P93 (community)`.
- Previous working DLL backed up locally before the update.
- Windows Smart App Control was **Off** during this particular test; no changes to mouse button mappings, macros or firmware.
- HID read-only sampler verified P93 `GET_FEATURE` returns report ID 7 with the expected command family.

## Settings persistence
- Plugin reads/writes user-local Qt INI settings.
- With `rgbEnabled=true` and `notificationsEnabled=true`, restarting OpenRGB restored RGB control and bound loopback `127.0.0.1:45893`.
- Last colors were persisted as 15 RGB triples in the INI file.
- After testing, `notificationsEnabled=false` was saved. A fresh OpenRGB restart loaded the controller and **did not bind port 45893**; `rgbEnabled=true` remained set.
- The beacon itself is **not automatically restarted**.

## Real HID effects — automated sampling

### Yellow alternating beacon (`P93:ALERT`)

The plugin was sent a localhost-only notification. Read-only HID `GetFeature` sampling observed a repeating pattern over approximately five seconds:

- Frame A: **7 slots** with `FF D2 00` (yellow), **8 slots** with `00 00 00` (off).
- Frame B: **7 slots** off, **8 slots** yellow.
- Frames alternated repeatedly before the timer stopped and configured colors were restored.

### Green completion signal (`P93:SUCCESS`)

- Read-only sampler observed all 15 HID slots set to `00 FF 00` (green) for approximately 1.8 seconds.
- Prior controller colors were restored afterward (the current saved OpenRGB selection at test time was black).

## Visual verification still needed

- Confirm whether the default group A/B split maps to the physical **left/right** mouse LEDs.
- Use **Identify next LED slot (yellow)** for a one-at-a-time physical mapping of the 15 HID slots (some may be unpopulated/linked).
- Verify the existing Bloody WorkShop screenshot button/macro functions after an OpenRGB restart.
- Observe the beacon and notify colors with the mouse in hand; the test confirms USB report state, **not camera-visible LED positions**.

Test data remained on the authorized Windows machine under `C:\Users\lauri\Portable\Scripts\RGB-Uuring\`. The public repo does not contain raw USB captures or user input events.

## Physical LED mapping update — 10 November 2026

The P93 owner has identified **eight** physical LEDs, not fifteen. The HID RGB report still contains fifteen triplet fields, but **only fields 1–8 correspond to physical LEDs**. Logo lighting uses 7 and 8 together; the wheel (LED 1) is the most conspicuous.

| Physical LED | HID slot | Location | RGB byte offsets |
|---:|---:|---|---|
| 1 | 1 | Wheel / middle button | 8–10 |
| 2 | 2 | Left front | 11–13 |
| 3 | 3 | Right front | 14–16 |
| 4 | 4 | Under three extra side buttons | 17–19 |
| 5 | 5 | Right middle | 20–22 |
| 6 | 6 | Left middle | 23–25 |
| 7 | 7 | Left rear and shared logo | 26–28 |
| 8 | 8 | Right rear / middle and shared logo | 29–31 |

The v0.2.1 beacon test above describes the **old 7-slot / 8-slot HID-field split** and remains useful as historical evidence that the mouse receives two distinct command frames. The **new visible LED grouping** proposed by the owner is **A = 1+4**, **B = 2+3+5+6+7+8**. The new v0.3.0 build and HID report verification are separate tests; do not interpret the original split as evidence that fifteen physical LEDs exist.

Original schematic and exact byte map: [LED_MAP.md](LED_MAP.md).
