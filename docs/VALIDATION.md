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

## True Mouse Art v0.3.0 — eight physical LEDs, new group split

- **Owner-confirmed physical LED count:** 8. Protocol includes 15 RGB triple fields, but only 1–8 are physically present. Slots 9–15 stay zero and are hidden from the OpenRGB UI.
- **Owner-confirmed layout:** 1 wheel, 2 left front, 3 right front, 4 below three extra buttons, 5 right middle, 6 left middle, 7 left rear, 8 right rear/center. Mouse logo is illuminated by 7 and 8 together.
- **Branding:** *True Mouse Art / Bloody P93 mouse OpenRGB Plugin / I Turned My Mouse into a Flashing Beacon!*; Estonian headline *Tegin hiirest vilkuri*.
- **Default new beacon:** alternating physical LEDs 1+4 with LEDs 2+3+5+6+7+8 (yellow `FF D2 00`).
- **Automated build:** [GitHub Actions run 42788972975](https://github.com/liikane/openrgb-bloody-p93/actions/runs/42788972975) passed both HID packet unit tests and Windows plugin DLL compilation.
- **Local installation:** v0.3 DLL SHA-256 `7491A558BFD3622BE2DCE38EA68C483973B281120D2D891C61513258EE05A036`; prior v0.2.1 DLL backed up locally. OpenRGB v1.1 log explicitly shows `[PluginManager] Registering RGB controller Bloody P93 (community)`.
- **Actual P93 HID test:** Sent `P93:ALERT` over local UDP. Read-only `HidD_GetFeature` recorded repeating 2-slot yellow/13-slot black report and 6-slot yellow/9-slot black report. Seven of the inactive slots are the P93's unused 9–15 positions. The test stopped after about five seconds and returned to the previous configured color. This proves the requested 2/6 split is sent to the physical device. **Which physical LEDs are lit at each moment still needs user visual confirmation.**
- **After test:** notifications disabled, UDP port 45893 closed, `rgbEnabled=true` remained persisted, OpenRGB restarted and P93 controller registered normally.
- **Still to check manually:** screenshot button/macro after v0.3 update; visually confirm the wheel and button-area blink against the six outer lights. These observations must not be claimed as verified before the owner confirms.

## True Mouse Art v0.4.0 — color dialog, corrected schematic, Windows notification bridge plan

- **Physical validation (user, 10 November 2026):** The v0.3 beacon does blink on the actual mouse and the other mouse functions still work. Physical positions further clarified: LED 4 is **directly behind the wheel** (rather than to the side); other front/middle/rear LEDs are on the **sides of the mouse**, not flat on the top panel.
- **v0.4.0 UI:** Adds two `QColorDialog` picker buttons under OpenRGB **Settings → Bloody P93**, for independent **Group A** and **Group B** colors. The existing `Beacon interval` spin box controls speed from 120 to 2000 ms. Selected colors are stored in local QSettings keys `beaconColorA` and `beaconColorB`; default both `#FFD200`.
- **Notification semantics:** Manual beacon and `P93:ALERT` use chosen A/B colors; `P93:ERROR` overrides both groups red for 5 seconds; `P93:SUCCESS` displays temporary green. After the event the original OpenRGB selected colors return.
- **Updated original SVG diagram** with LED 4 behind scroll wheel and other lights on the left/right mouse outline. Manuals mention related HID hardware across other manufacturers as **research opportunities**, never claim another mouse model is automatically supported.
- **GitHub Actions** C++ packet unit tests and Windows DLL build passed: https://github.com/liikane/openrgb-bloody-p93/actions/runs/42794419671
- **Installed OpenRGB 1.1 DLL** on LAURIDELL, OpenRGB log confirms `Registering RGB controller Bloody P93 (community)`. Working v0.3 DLL saved under `C:\Users\lauri\Portable\Scripts\RGB-Uuring\OpenRGB-P93-v040\P93-v030-backup-20261110-115522.dll`. v0.4 DLL SHA-256 `A3A65E0812ADAA18E1ED7C3D22D35EA907758FC08312EAAEDD15EA8FB9512F7E`.
- **Real P93 HID readback test with two custom colors:** A `#00B7FF` on **2 HID slots** (1+4); B `#FF00AA` on **6 slots** (2+3+5+6+7+8), alternated repeatedly for `P93:ALERT` as instructed. Seven unused slots 9–15 stayed black.
- **Error override test:** `P93:ERROR` showed **2 red slots** alternating with **6 red slots**, ~5 seconds, then restored the selected colors.
- **After testing:** original user INI restored from `preferences-before-color-test.ini`, `rgbEnabled=true`, `notificationsEnabled=false`, UDP port 45893 closed. OpenRGB restarted and loaded plugin normally. Mouse button remapping, macro assignments and firmware were not changed.
- **Further manual user check:** open new **Group A color / Group B color** dialog buttons and verify visual preview and saving after restarting OpenRGB. HID color generation and restoration are already verified from protocol readback.
- **Windows notification integration:** standalone privacy-first tray bridge design published under `docs/WINDOWS_NOTIFICATIONS.md`. Separate GitHub issue #5 is open. It requires explicit Windows notification access permission and an app allowlist; no new software has been silently installed.
## True Mouse Art v0.5.0-beta.1 — persistent alerts and 8-LED idle color animation (10 Nov 2026)

**Device:** Bloody P93 physical USB HID interface, Windows LAURIDELL, OpenRGB 1.1.

### Build and installation

- GitHub Actions run 42903527652: Python notification bridge tests, native C++ P93 protocol/palette tests and MSVC/Qt 6.8.3 Windows plugin build all passed.
- New DLL SHA-256: B176B72C2B18833CBE6950E1AB84A73EBAC18BA821F3B32C77DCC7E32CC530A1.
- Installed v0.5 plugin to user OpenRGB plugin directory. Former v0.4 DLL backed up in local RGB-Uuring/OpenRGB-P93-v050/P93-v040-backup-20261110-231916.dll; preference file also backed up.
- OpenRGB log explicitly showed registration of RGB controller Bloody P93 (community).

### Verified with real mouse HID readback

1. **Eight LED idle state:** all 8 physical RGB positions were nonblack and rotating through distinct colors every ~550 ms. The 7 unused report fields stayed black. Verified with read-only HidD_GetFeature samples over 6 seconds.
2. **Persistent ERROR:** sent local ERROR event. Mouse alternated two red RGB slots (LED 1+4) with six yellow RGB slots, without the previous five-second timeout.
3. **Concurrent SUCCESS:** sent SUCCESS while ERROR remained pending. The readback showed two green RGB slots alternating with six white slots, then returned to the red/yellow category. Two event categories alternated for more than 20 seconds; settings contained pendingEvents=ERROR, SUCCESS.
4. **OpenRGB restart:** confirmed P93 registered again and pendingEvents=ERROR, SUCCESS remained persisted. Readback observed both error and completion palettes *after restart*, not just their presence in the INI file.
5. **Acknowledgement:** sending local P93:ACK cleared the pending event categories. Readback immediately showed the full eight-LED nonblack moving rainbow animation, not black. Settings showed no pending events.
6. **Bridge global hotkey registration:** local ntfy bridge log reported Global acknowledgement hotkey registered: Ctrl+Shift+F12. The actual human keypress event has not yet been verified; explicit ACK UDP handling was verified.

### Automatic startup

- Configured two per-user Windows scheduled tasks: True Mouse Art Notification Bridge (existing, starts headless ntfy/Windows event bridge), and OpenRGB - True Mouse Art (new, starts OpenRGB minimized using the supported --startminimized argument).
- Both are ordinary interactive-user startup tasks; no admin service, no mouse button remapping. Full sign-out/sign-in exercise still awaits the user.

### Safety and limits

- Event queue capacity: 16 categories, each with its distinct pair of flashing colors, 2 full A/B cycles per category before showing the next.
- Persistent alert phase length at least 500 ms; idle RGB cycle defaults to 550 ms per step.
- Stored categories and idle preferences do not include ntfy message text, subjects, or identities.
- P93 button assignments/macros/firmware have not been changed by this release; direct physical macro test for v0.5 still to be confirmed.
- During locked Windows sessions or when the PC is asleep, hardware visibility depends on OS/USB power and whether OpenRGB is running. Alerts are persistent after *receipt by the running plugin*, not guaranteed for messages sent while the computer or OpenRGB is offline.

**Instructions:** [PERSISTENT_ALERTS.md](PERSISTENT_ALERTS.md). Source state machine: src/P93Signals.h and src/BloodyP93Plugin.cpp.
