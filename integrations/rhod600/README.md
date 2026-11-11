# Genesis Rhod 600 RGB — six-zone notification adapter

**True Mouse Art / Vilgutaja research extension.** A Windows-only, free/open-source Python 3 adapter that can control the six keyboard lighting zones and receive the same local NTFY/Windows event codes as the Bloody P93 plugin.

**Status, 11 November 2026:** RGB protocol mapped and hardware HID writes accepted; short local alert queue + acknowledgement test passed. **The owner has not yet visually confirmed the final six-zone patterns**, and a full Windows sign-out/sign-in test remains outstanding.

## Hardware identity and verified report

- USB **VID 1A2C / PID 8000**, collection **MI_01 / COL07**
- HID UsagePage **0xFF01**, Usage **0x0001**
- Feature and Output lengths **8 bytes**, Input report length **0**
- Windows API: `HidD_SetFeature`; no custom driver or modified firmware
- Exactly **six AREAs**, each using one 4-bit color index, not individual-addressable RGB.

The actual manufacturer reports recorded by the keyboard owner on 11 November 2026 identified the full lighting report:

```text
07 FF 70 [AREA1<<4|AREA2] [AREA3<<4|AREA4] [AREA5<<4|AREA6] 03 00
```

| Color index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| Keyboard color | Off | Red | Green | Blue | Yellow | Cyan | Purple | White |

**Owner-captured sequences:**

- `07 FF 70 31 11 11 03 00` → `32` → `33`: AREA2 red, green, blue
- `07 FF 70 73 11 11 03 00` → `63` → `53`: AREA1 white, purple, cyan
- Earlier owner capture: `07 FF 70 00 00 00 03 00`, `60 00 00`, `61 00 00`, `61 60 00`, `61 60 60`

Other vendor command families (`07 FF 20`, `07 FD`, `07 FB`, `07 FC`, `07 FA`, `07 F0`) have **not** been classified as lighting-only and are **never transmitted by this adapter**.

**Important:** Other keyboard models may share VID/PID `1A2C:8000`. The driver checks the exact interface and all HID usage/report lengths, and refuses to run unless exactly one matching device exists. It also refuses to send lighting reports while `ShinetekTools.exe` is running to avoid two simultaneous controllers.

## Attention patterns

| Event | AREA1/3/5, phase A | AREA2/4/6, phase A | In phase B |
|---|---|---|---|
| `ERROR` | Red | Yellow | Reverse colors |
| `ALERT` | Red | Blue | Reverse colors |
| `SUCCESS` | Green | White | Reverse colors |
| `NOTICE` | Green | Yellow | Reverse colors |

Frames alternate every **950 ms**; all six AREAs stay lit, changing colors rather than strobing black. Several pending categories rotate: two complete A/B cycles each, then the next event; maximum 16. Categories survive a daemon restart, with no notification text stored.

`ACK` or `STOP` clears the pending queue. Without alerts, all six AREAs continuously rotate through a six-color idle pattern (purple, yellow, cyan, green, blue, white), with **no all-black idle frame**. Existing P93 global shortcut **Ctrl+Shift+F12** sends ACK to both devices through the local NTFY bridge.

## Running and testing

Python 3 standard library only. No installable dependency is required for RGB control. Windows 10/11.

```powershell
$base = "C:\Users\lauri\Portable\OpenRGB-Bloody-P93-Plugin\integrations\rhod600"

# No writes: check physical interface and show command previews.
python "$base\daemon.py" --probe
python "$base\daemon.py" --dry-run
python "$base\test_protocol.py"

# A single opt-in 8-byte RGB report (user-confirmed pattern).
python "$base\daemon.py" --one-shot 5,3,1,1,1,1 --enable-hardware

# Run a temporary 25-second direct-hardware signal service.
python "$base\daemon.py" --serve --enable-hardware --duration 25
```

The background service listens **only** on `127.0.0.1:45894`. While running, test from another PowerShell window:

```powershell
python "$base\daemon.py" --event ERROR
python "$base\daemon.py" --event SUCCESS
python "$base\daemon.py" --event ACK
```

For a permanent, user-level login task:

```powershell
& "$base\Manage-RhodTask.ps1" -Mode Install
& "$base\Manage-RhodTask.ps1" -Mode Status

# To pause the adapter without uninstalling:
& "$base\Manage-RhodTask.ps1" -Mode Stop

# Remove background service and login task:
& "$base\Manage-RhodTask.ps1" -Mode Uninstall
```

**Existing NTFY integration:** `integrations/ntfy/bridge.py` sends one event to both `127.0.0.1:45893` (P93) and **45894** (optional Rhod adapter), without transmitting message text to either. The bridge's existing `ACK` hotkey clears both. The keyboard works without OpenRGB; the P93 still uses its OpenRGB plugin.

**Previous RGB state:** The HID Feature readback `07 00 00 00 00 00 00 00` does *not* reveal the six current colors. The adapter cannot perfectly restore an unknown vendor-program color state automatically. Only the last owner-recorded layout `07 FF 70 53 11 11 03 00` can be explicitly reapplied if desired. Opening the official ShinetekTools GUI can restore a manufacturer profile; stop this adapter before doing so.

## Privacy and safety

- No keyboard input is captured, remapped, hooked or transmitted.
- No macro, DPI, profile or firmware commands are sent; only the known `07 FF 70` lighting report.
- No custom kernel driver, elevated Windows service, cloud credentials or new subscription is required.
- NTFY topic credentials remain in the owner's private `Portable/Automation/Summary/settings.json`, **not in GitHub**.
- The optional earlier Frida inspection tooling is **not used in the live lighting adapter**.
- Close ShinetekTools first. Starting it while the adapter runs causes RGB writes to pause.
- To avoid excessive flashing, frames change every ~950 ms; all zones stay lit. Reduce or stop animation with the `-Mode Stop` command.
- Some hardware settings may persist when the adapter exits. This application does not attempt an unknown restore command.

## Files

- [protocol.py](protocol.py) — pure six-area encoding, palettes, no hardware
- [hid.py](hid.py) — strict Windows HID identity checks and opt-in color-only SetFeature
- [daemon.py](daemon.py) — local six-zone NTFY/Windows event receiver, persistent categories, idle animation
- [test_protocol.py](test_protocol.py) — original captured reports, bounds, alerts, queue, idle tests
- [Manage-RhodTask.ps1](Manage-RhodTask.ps1) — optional per-user startup/stop/uninstall
- [probe_readonly.py](probe_readonly.py) — read-only hardware inventory
- [inspect_vendor_pe.py](inspect_vendor_pe.py), [trace_vendor_feature.py](trace_vendor_feature.py) — research tools (not needed to use adapter)

See [GitHub issue #4](https://github.com/liikane/openrgb-bloody-p93/issues/4) for the research and hardware validation checklist. This is an independently researched community implementation, not an official Genesis driver.
