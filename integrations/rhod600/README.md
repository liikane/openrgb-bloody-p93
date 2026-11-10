# Genesis Rhod 600 RGB — protocol research

**Status:** Hardware identified, HID reports confirmed, RGB packet content **not validated**. No experimental vendor command has been sent to the keyboard.

## Hardware (LAURIDELL, 11 November 2026)

- Keyboard USB `VID 1A2C / PID 8000`.
- Vendor HID interface `MI_01 / COL07`, `UsagePage 0xFF01`, `Usage 0x0001`.
- HID report `ID 0x07`, exactly **8 bytes** for Output and Feature. Input report length on this collection = 0.
- Read-only `HidD_GetFeature` on ID 7 returns `07 00 00 00 00 00 00 00`, which is **not** a documented current RGB color report.
- Six lighting zones and nine hardware modes, as documented by the manufacturer. Via hardware keys, the owner can use `Fn+1` to `Fn+9`, and `Fn+7` for custom mode. **No app-side RGB control has been proven yet.**

**Important:** Other keyboards use the same `1A2C:8000` USB ID. A future Rhod driver must verify the exact HID interface, UsagePage/Usage, report sizes and a proven protocol signature; VID/PID alone is insufficient.

## Manufacturer software

- `C:\Program Files (x86)\Rhod 600 RGB\ShinetekTools.exe` is installed; at the 2026-11-11 check it was running.
- Manufacturer `config.xml` declares `vid=1a2c, interface=1, subdevice=7` and `pid=0` (wildcard); this aligns with our `COL07` interface. **Do not reuse this wildcard in our own adapter.**
- Both vendor executable and `utilities.dll` are x86 native PE binaries. The installed EXE imports `HidD_SetFeature`, `HidD_GetFeature`, `WriteFile` and `ReadFile`.
- Static-only disassembly found 8-byte outgoing Feature command **candidates** beginning `07 FD`, `07 FB`, `07 FC`, `07 FA` and `07 F0`. Their meaning is **unknown**; some may set macros, profiles or persistent settings. **Never send these commands as experiments until lighting-only semantics are confirmed.**
- At this inspection the system registry indicated Smart App Control had already been switched off (policy state 0). This investigation **did not change** any Windows protection settings. Previously an installer DLL had been blocked by Smart App Control.

## Tools prepared

| File | Purpose | USB writes? |
|---|---|---|
| `probe_readonly.py` | Enumerate the Rhod HID interfaces and query only report 7 | **None** |
| `inspect_vendor_pe.py` | Inspect PE imports/ASCII strings of local vendor binaries, without launching them | **None** |
| `trace_vendor_feature.py` | Optional short Frida user-mode trace of only *outgoing* 8-byte vendor reports from the Shinetek program | **None initiated by tracer** |
| `Capture-Rhod600.ps1` | Start a 30-second trace of the currently running vendor process and save output only to the local investigation folder | **None initiated by tracer** |

The optional open-source Frida package is currently installed **only** in `Portable\Scripts\RGB-Uuring\analysis-deps`. No kernel driver, USBPcap or global keyboard logger is installed by this research code.

### Next actionable experiment

With the manufacturer's ShinetekTools RGB configuration window open, run in Windows PowerShell 7:

```powershell
& "C:\Users\lauri\Portable\OpenRGB-Bloody-P93-Plugin\integrations\rhod600\Capture-Rhod600.ps1"
```

While it is capturing, change **one lighting color or effect**, not the macro/profile settings, using the manufacturer's GUI. The tool stops after 30 seconds. Compare the captured `OUT` reports against idle baseline; identify the exact command that changed RGB lighting and how the six zones are encoded. A preliminary 12-second idle capture observed **zero outgoing reports**, as expected when no settings changed.

After a confirmed lighting-only packet exists, write a separate **Rhod 600 OpenRGB device driver/adapter** sharing event categories with True Mouse Art. Do not reuse the Bloody P93's 64-byte HID protocol.

### Safety

Never transmit arbitrary HID Feature/Output data to this keyboard; the 8-byte vendor channel may also manage programmed macro profiles. No Fn mappings, macro definitions, firmware, Windows security policy or existing mouse lighting integration were changed by this investigation.

Manufacturer's manual: https://download.genesis-zone.com/Manuals/Rhod_600_RGB_Genesis_manual_WEB.pdf

A related but different keyboard with the same USB ID (not proof of matching lighting packets): https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues/3022
