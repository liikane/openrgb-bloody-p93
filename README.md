# OpenRGB Bloody P93 RGB Bridge

**Experimental OpenRGB 1.1 plugin for the Bloody P93 gaming mouse.**

Adds Bloody P93 RGB support to OpenRGB through **Plugin API v5**, without modifying OpenRGB itself or installing USB capture drivers.

Built by [liikane](https://github.com/liikane). Contributions and testing are welcome.

## Verified hardware and protocol

| Item | Value |
| --- | --- |
| Mouse | Bloody P93 |
| USB VID:PID | `09DA:31DE` |
| HID interface | `MI_02 / COL04` |
| HID Usage Page / Usage | `0xFF32 / 0x0218` |
| Feature report | ID `0x07`, 64 bytes |
| Commands | `07 03 06 01` (initialize), `07 03 06 00` (direct mode), `07 03 06 02` (RGB color) |
| Confirmed on hardware | Static purple (`160,0,255`), red/green flashes |
| Host target | OpenRGB 1.1, Windows x64, Qt 6.8.3 |

A real Bloody P93 on Windows was tested. The standard OpenRGB release did not recognize this PID, despite recognizing other Bloody mouse models.

## Features

- Shows **Bloody P93 (community)** in OpenRGB's Devices list via a Plugin API v5 virtual controller.
- Single RGB color control across the mouse LEDs, including color changes from the OpenRGB SDK and effects.
- An **Enable RGB control** checkbox: no HID writes are sent when the plugin loads; you must opt in.
- No button remapping, macro writes, DPI changes, firmware updates, or proprietary driver installation.
- Direct Windows HID transport (SetupAPI and HID DLL).

**Limitations:** first preview, Windows only. Individual LED mapping is not established; all 15 known protocol slots receive the same color. Mode persistence and restoring original hardware lighting behavior after disabling the plugin have not yet been validated. Only use with the exact VID:PID and HID collection above.

## Installation (after a successful build)

1. Use the DLL from a successful [GitHub Actions](../../actions/workflows/build-windows.yml) run; **do not download an unverified executable**.
2. Make sure you use **OpenRGB 1.1** on Windows x64; stop other utilities from changing the mouse lighting at the same moment.
3. Open OpenRGB's plugin manager and install `OpenRGBBloodyP93Plugin.dll` (or place the DLL in the configured plugins directory, then restart OpenRGB).
4. Find **Bloody P93 RGB Bridge** under the plugin settings. The mouse should appear as **Bloody P93 (community)** when connected.
5. In the plugin settings, tick **Enable RGB control (experimental)**.
6. In OpenRGB Devices select **Bloody P93 (community)** and change the Direct color.

If the device does not appear, check the USB identity and the OpenRGB logs. The standard OpenRGB detector does not support this mouse until the plugin is installed.

## Build from source

This project is a standalone **Qt 6 / C++17** plugin. Build it against OpenRGB release `release_1.1` (Plugin API 5). On Windows use Qt **6.8.3** with MSVC 2022 to match OpenRGB's distributed Qt runtime.

```powershell
git clone --branch release_1.1 https://github.com/CalcProgrammer1/OpenRGB.git openrgb
$env:OPENRGB_SOURCE_DIR = (Resolve-Path .\openrgb).Path
qmake OpenRGBBloodyP93Plugin.pro
nmake
```

The produced DLL is in `dist/`. GitHub Actions builds the Windows version automatically.

## Safety

The plugin does not connect to arbitrary HID devices; it checks `09DA:31DE`, `COL04`, the HID usage, report size and vendor report prefix before writing anything. The only HID writes are known RGB-mode and color reports. Hardware RGB color may persist after closing OpenRGB, depending on mouse firmware; restore your saved Bloody Workshop 8 profile if needed.

The source code is **GPL-2.0-or-later**. The project is independently maintained; it is not an official Bloody or OpenRGB release.

## Roadmap

- [ ] Confirm plugin's Windows DLL builds and loads in OpenRGB 1.1.
- [ ] Test OpenRGB color picker and SDK event signals with the physical P93.
- [ ] Verify LED mapping, DPI and macro preservation, reconnection, and cleanup.
- [ ] Add automated simulated-HID regression tests.
- [ ] Request a listing in the official [OpenRGB plugin catalog](https://openrgb.org/plugins) after a validated binary release.
- [ ] Submit upstream device-support improvements to [OpenRGB on GitLab](https://gitlab.com/CalcProgrammer1/OpenRGB) for broader integration.

## Project status

**Experimental source release:** not yet accepted into the official OpenRGB plugin catalog. Check GitHub Actions build status and the Releases page for tested downloads.
