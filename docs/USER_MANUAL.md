# True Mouse Art — User manual

**Bloody P93 mouse OpenRGB Plugin**

*I Turned My Mouse into a Flashing Beacon!*

A perfectly respectable RGB gaming mouse had eight lights, but wasn't allowed to tell its computer user very much. We gave it a more interesting job: signal task completion, errors, and attention-worthy events without popups. The mouse still works as a mouse. It's a hobby project with real HID commands, not an official Bloody/OpenRGB extension.

### Exploring other manufacturers' mice

Hardware is often surprisingly similar across gaming mice. Investigate USB/HID controller IDs, collection IDs, feature report sizes and vendor RGB commands; sometimes a related model can use comparable control logic. The **present DLL supports only the exact Bloody P93 USB/HID identity**. Never assume a matching command layout solely from a familiar-looking mouse or transmit unknown vendor commands without verifying them first.

## 1. Requirements and installation

**Windows 10/11, OpenRGB 1.1**, Bloody P93 gaming mouse (USB `09DA:31DE`).

1. Download the latest matching `OpenRGBBloodyP93Plugin.dll` from [Releases](https://github.com/liikane/openrgb-bloody-p93/releases). Check the release notes and SHA-256 for experimental builds.
2. Exit OpenRGB fully, including any tray instance, and make a backup copy of an existing plugin DLL.
3. Copy the new DLL into `%APPDATA%\OpenRGB\plugins` (create the folder if required).
4. Restart OpenRGB. Open **Settings → Bloody P93**, then check **Enable RGB control**.
5. Under **Devices → Bloody P93 (community)**, you should see **eight physical LED controls**.

The plugin requires neither a custom HID driver nor PawnIO. Windows Smart App Control may block unsigned builds; verify the source of a release and be aware of security implications before changing system security settings.

## 2. Where the eight lights are

![Top view diagram of the P93 mouse and its eight mapped LEDs](mouse-led-map.svg)

**Wheel LED 1** is especially visible. The mouse logo is illuminated by **LEDs 7 and 8 together**. The sketch is an original simplified top-view map, not an official manufacturing diagram.

| LED | HID slot | Physical position | RGB byte offsets (R,G,B) |
|---:|---:|---|---|
| 1 | 1 | Wheel / middle button | 8, 9, 10 |
| 2 | 2 | Left front | 11, 12, 13 |
| 3 | 3 | Right front | 14, 15, 16 |
| 4 | 4 | Middle, directly behind the wheel | 17, 18, 19 |
| 5 | 5 | Right middle | 20, 21, 22 |
| 6 | 6 | Left middle | 23, 24, 25 |
| 7 | 7 | Left rear; also the logo | 26, 27, 28 |
| 8 | 8 | Right rear / center; also the logo | 29, 30, 31 |

**Important:** there are **8 physical LEDs**, not 15. The vendor's 64-byte HID report has 15 RGB triplet *fields*, but **slots 9–15 have no corresponding P93 LEDs** and are hidden in the OpenRGB interface. Their bytes remain present and are transmitted as zero. See the complete [LED map](LED_MAP.md).

## 3. Change colors

Open **Devices**, choose the P93 mouse, click any of its eight LEDs, then select a color via the color wheel or Hex field. Click **Apply Colors To Selection** if required. Color examples:

- Purple: `#A000FF`
- Yellow: `#FFD200`
- Red: `#FF0000`
- Green: `#00FF00`

RGB enablement and the eight color selections persist after OpenRGB restarts. **Saving Not Supported** on the device page refers to storing settings in hardware firmware, not to the plugin's application-level settings.

## 4. The flashing beacon

The default effect has **two complementary groups**. It is more interesting than switching all the lights on and off simultaneously:

| Phase | Yellow LEDs | Off LEDs |
|---|---|---|
| **A** | **1 + 4**, the wheel and the LED directly behind it | 2, 3, 5, 6, 7, 8 |
| **B** | **2 + 3 + 5 + 6 + 7 + 8**, perimeter and logo | 1, 4 |

Go to **Settings → Bloody P93**. Adjust group A/B slot numbers or **Beacon interval** (120–2000 ms), then check **Flashing beacon**. To stop, uncheck it or click **Restore selected OpenRGB colors**.

These groups alternate center versus perimeter, **not literal left versus right**. Beacon flashing does *not* resume automatically after restarting OpenRGB.

### Customize colors and flashing speed

Go to **Settings → Bloody P93**. Press **Group A color** and **Group B color** to open separate color-picker dialogs. Set colors for each group; the two color selections are persisted across application restarts. **Beacon interval** (120–2000 milliseconds) controls the alternation rate. Low values flash faster; use moderate rates if flashing is distracting.

Manual beacon and `ALERT` use the saved group colors. `ERROR` temporarily flashes red regardless of the saved colors; `SUCCESS` briefly lights the eight LEDs green.

## 5. Notifications

Enable **Local notification commands** under Settings to allow a local app to signal the mouse via `127.0.0.1:45893`. This listener is disabled unless you opt in and cannot be accessed by other machines.

The repository includes a PowerShell helper:

```powershell
.\Send-P93Notification.ps1 -Event ALERT
.\Send-P93Notification.ps1 -Event ERROR
.\Send-P93Notification.ps1 -Event SUCCESS
.\Send-P93Notification.ps1 -Event STOP
```

| Command | Outcome |
|---|---|
| `ALERT` / `NOTICE` | Alternating yellow beacon for 5 seconds |
| `ERROR` | Alternating red beacon for 5 seconds |
| `SUCCESS` | Eight LEDs glow green for 1.8 seconds |
| `STOP` | Stop effects and restore your selected RGB colors |

A local script, task monitor, or ntfy client can invoke this helper when an event occurs. The plugin **does not directly connect to ChatGPT or subscribe to an ntfy server**.

## 6. Troubleshooting

| Symptom | Resolution |
|---|---|
| No plugin settings | Check DLL folder and restart OpenRGB fully |
| No P93 device | Verify the P93 model and choose **Retry device detection** |
| Colors don't change | Enable RGB control, select the physical LED and apply color |
| Colors revert | A second RGB program might be controlling the same mouse |
| PawnIO warning | PawnIO is not needed for this particular USB HID interface |
| Windows blocks DLL | Check the downloaded build and code-signing status; Smart App Control has no per-file exemption |
| Notifications don't work | Enable notifications and check whether loopback port 45893 is free |
| Slots 9–15 are absent | Correct: those fields have no P93 physical LEDs |
| Mouse stops responding | Close OpenRGB, reconnect the device, and restore the previous plugin if necessary |

OpenRGB logs: `%APPDATA%\OpenRGB\logs`. Do not share full raw USB traces, as they can include traffic from unrelated devices.

## 7. Uninstall or restore lighting

Exit OpenRGB, delete `%APPDATA%\OpenRGB\plugins\OpenRGBBloodyP93Plugin.dll`, and restart. To restore an earlier lighting pattern, load your saved Bloody WorkShop 8 profile. This plugin never writes your mouse-button mappings or firmware.

## 8. Windows notification integration

The plugin accepts local UDP commands but does not read Windows notifications by itself. See the [independent Windows notification bridge design](WINDOWS_NOTIFICATIONS.md): this requires explicit Windows notification access permission, filters, and a separate lightweight tray process.

## 9. Technical documentation and support

HID identity `VID_09DA/PID_31DE`, `MI_02/COL04`, `UsagePage=0xFF32`, `Usage=0x0218`. RGB command `07 03 06 02`, 64-byte `HidD_SetFeature` report ID `07`. Physical LED RGB byte offsets 8–31.

See [LED map and diagram](LED_MAP.md), [HID protocol](HID_PROTOCOL.md), [validation notes](VALIDATION.md), or [GitHub source and issues](https://github.com/liikane/openrgb-bloody-p93). License GPL-2.0-or-later.
