# True Mouse Art

**Bloody P93 mouse OpenRGB Plugin**

*I Turned My Mouse into a Flashing Beacon!*

The mouse was already full of lights. It seemed a shame to let it sit there doing nothing useful.

What if a running task could finish and the mouse could glow green? What if an error could flash red? What if a reminder could flash a yellow pattern — without stealing keyboard focus, covering the screen, or making Windows beep? It may not qualify as serious automotive engineering, but it's a good excuse to turn a gaming mouse into a tiny personal signaling system.

**True Mouse Art** is a free and open-source [OpenRGB](https://openrgb.org/) plugin for the **Bloody P93**. It lets the computer send RGB colors, a simple center-versus-perimeter beacon, and local automation notifications to the mouse.

[![Build](https://github.com/liikane/openrgb-bloody-p93/actions/workflows/build-windows.yml/badge.svg)](https://github.com/liikane/openrgb-bloody-p93/actions/workflows/build-windows.yml) ![License](https://img.shields.io/badge/license-GPL--2.0--or--later-green) ![OpenRGB](https://img.shields.io/badge/OpenRGB-1.1-blue)

**Developed by [liikane](https://github.com/liikane)** · [Releases](https://github.com/liikane/openrgb-bloody-p93/releases) · [Eesti keeles](README.et.md) · [Manual](docs/USER_MANUAL.md)

## Other mice? Try investigating, not blindly applying commands

Many gaming mice use similar USB/HID controller families, even across different brands. It is worth **researching** whether your mouse has comparable LED lighting hardware and protocol structure. Start by identifying its USB VID/PID, HID collections, Usage Page, report length, and the original manufacturer's RGB commands. **Do not send P93 reports to an unverified mouse.** The plugin intentionally supports **Bloody P93 (09DA:31DE)** only; supporting other models requires separate capture, verification, tests, and an explicit device entry.

## A mouse with eight lights and a mission

![Bloody P93 LED schematic](docs/mouse-led-map.svg)

The P93 has **8 physical RGB LEDs**, each available individually in OpenRGB, not 15 physical LEDs. The vendor's 64-byte HID report contains 15 RGB fields, but **fields 9–15 are unused** on this mouse and remain hidden from the user. The very visible wheel is LED **1**; the logo is illuminated by **7 and 8 together**.

**The default flashing beacon alternates:**

- **Phase A:** LEDs **1 + 4** — wheel and the area immediately behind the wheel.
- **Phase B:** LEDs **2 + 3 + 5 + 6 + 7 + 8** — front, sides, rear and logo.

Both phases are yellow initially; the unselected LEDs go dark. You can change the interval (120–2000 ms) or edit the groups in the plugin. The effect is a center/perimeter beacon, not a literal left/right emergency-vehicle lightbar.

[Exact LED positions, HID slot numbers and RGB byte offsets](docs/LED_MAP.md)

## What it does

| Feature | Status |
|---|---|
| OpenRGB detects Bloody P93 (`09DA:31DE`) | Tested on hardware |
| Change RGB color in the OpenRGB GUI | Tested on hardware |
| Eight individually addressable LED controls | Implemented; owner mapped positions |
| Alternating two-group beacon | HID output tested; revised 1+4 / remaining grouping requires visual confirmation |
| Local event commands `ALERT`, `ERROR`, `SUCCESS`, `STOP` | HID output tested |
| Remember settings when OpenRGB restarts | Tested in v0.2.1; retains RGB opt-in, slot colors, groups, interval |
| Preserve Bloody WorkShop button macros | Plugin never writes button mappings or firmware; previous physical button test passed |

### Customize the beacon

Under **Settings → Bloody P93**, choose **Group A color** and **Group B color**. Either button opens a normal Windows/Qt color-picker dialog. You can choose different colors for the two alternating LED groups; the colors survive a restart. **Beacon interval** is the existing speed field (120–2000 ms): a smaller number means faster alternation.

Manual beacons and `ALERT` use your chosen colors. `ERROR` temporarily overrides both to red and `SUCCESS` shows green. Normal colors return after the notification.

## Install and try

1. Download the latest **compatible Windows DLL** from [Releases](https://github.com/liikane/openrgb-bloody-p93/releases). Verify the release notes before using a prerelease.
2. Exit OpenRGB 1.1 completely, including the system tray.
3. Copy `OpenRGBBloodyP93Plugin.dll` to `%APPDATA%\OpenRGB\plugins` (create the folder if needed).
4. Restart OpenRGB, open **Settings → Bloody P93** and check **Enable RGB control**. The setting is remembered.
5. In **Devices → Bloody P93 (community)** change any of the **eight** LED colors.
6. For the beacon, return to **Settings → Bloody P93**, adjust the groups or interval and check **Flashing beacon**.

The beacon does not automatically start flashing after a restart, to avoid unwanted surprises. Notifications are disabled unless you opt in.

## Let the computer signal something

Optionally enable **Local notification commands** in plugin settings. The plugin listens only on the local computer at `127.0.0.1:45893`.

```powershell
.\Send-P93Notification.ps1 -Event ALERT    # Yellow group beacon for 5 seconds
.\Send-P93Notification.ps1 -Event ERROR    # Red group beacon for 5 seconds
.\Send-P93Notification.ps1 -Event SUCCESS  # All eight LEDs green for 1.8 seconds
.\Send-P93Notification.ps1 -Event STOP     # Restore OpenRGB-selected colors
```

A PowerShell job, local ntfy client, task monitor, or another automation can invoke the sender. **The plugin itself does not monitor ChatGPT or subscribe to external ntfy servers.** Those integrations need their own triggering component.

### The hardware trick

Windows HID Feature report **0x07**, **64 bytes**, identity `VID 09DA / PID 31DE`, collection `MI_02/COL04`. A static-color command begins `07 03 06 02` followed by the eight RGB triples at bytes 8–31. The rest of the vendor packet remains intact.

See the [documented command protocol](docs/HID_PROTOCOL.md), which includes the byte-by-byte LED map and safe examples. This is an independently reverse-engineered community project, **not an official Bloody API**.

## Full documentation

- [English user manual](docs/USER_MANUAL.md)
- [Eestikeelne kasutusjuhend](docs/KASUTUSJUHEND.md)
- [Mouse diagram and LED/HID byte table](docs/LED_MAP.md)
- [Full HID protocol reference](docs/HID_PROTOCOL.md)
- [Windows notifications bridge — design and privacy](docs/WINDOWS_NOTIFICATIONS.md)
- [Hardware verification notes](docs/VALIDATION.md)
- [The portfolio story / case study](docs/CASE_STUDY.md)

## Build and security

GitHub Actions automatically builds the plugin for **OpenRGB 1.1**, Windows x64, **Qt 6.8.3**, MSVC 2022, and runs C++ HID packet tests. The plugin uses built-in Windows HID and Winsock2, without a custom driver or a Qt Network dependency. Hardware RGB control is strictly opt-in; no firmware or button configuration commands are sent. Unchecked beacon groups or unsupported device IDs are rejected.

**Windows Smart App Control may block unsigned prerelease DLLs.** A code-signing plan is being explored for wider distribution. Prefer trusted, verifiable builds, and never disable security protections without assessing the trade-offs.

The plugin is available under **GPL-2.0-or-later**. It is independent of both Bloody and the OpenRGB project.

*Next adventure: can we teach a Genesis Rhod 600 keyboard to react to events too?*

## Notifications: ntfy + selected Windows events

A small Python bridge subscribes to an existing **ntfy** channel and to four selected Windows Event Log events, mapping them to the plugin's local ALERT / NOTICE / ERROR / SUCCESS signals. It runs in the background and can start at Windows logon. It needs **no extra Python packages**, stores no raw notification text, and does not change mouse macros.

See [installation and configuration](integrations/ntfy/README.md), [real-hardware integration test](integrations/ntfy/VALIDATION.md), and the separate [Windows Toast notification roadmap](docs/WINDOWS_NOTIFICATIONS.md). **Windows Event Log events are not the same as arbitrary Windows notification-center Toasts.**
