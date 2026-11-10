# Bloody P93 RGB Bridge — User Manual

**Requirements:** Windows 10/11, OpenRGB **1.1**, Bloody **P93**.  
**Project:** [liikane/openrgb-bloody-p93](https://github.com/liikane/openrgb-bloody-p93)  
**Downloads:** [GitHub Releases](https://github.com/liikane/openrgb-bloody-p93/releases)  
**Status:** Independent community plugin tested on physical Windows hardware. Not an official product of Bloody or OpenRGB.

## 1. What it does

This plugin adds **Bloody P93 (community)** to the OpenRGB Devices list, allowing you to control **15 HID RGB color slots** from OpenRGB. It uses built-in Windows HID APIs and requires no custom USB driver. It **does not modify mouse button assignments, macros, DPI settings, or firmware**.

Supported USB identity: `09DA:31DE`; HID interface `MI_02/COL04`. The plugin is not intended for other Bloody models.

## 2. Installation

1. Download `OpenRGBBloodyP93Plugin.dll` from the project's [GitHub Releases](https://github.com/liikane/openrgb-bloody-p93/releases). Match the build to OpenRGB 1.1 on Windows x64.
2. Exit OpenRGB completely, including its system tray instance.
3. Copy the DLL into this directory:

   `%APPDATA%\OpenRGB\plugins\`

   Create the `plugins` folder if it does not exist. Alternatively, install the DLL via OpenRGB's **Settings → Plugins** interface.
4. Restart OpenRGB. You should now see a **Bloody P93** settings page and **Bloody P93 (community)** under Devices if a matching mouse is connected.

Do not register the DLL in Windows system directories. Administrator permissions are not needed.

## 3. Changing colors

1. Open **Settings → Bloody P93**.
2. Verify that the device is connected. If not, click **Retry device detection**.
3. Check **Enable RGB control (experimental)**. Before you enable it, the plugin sends no RGB commands.
4. Go to **Devices** and select **Bloody P93 (community)** on the left.
5. Select the colored square labeled **All RGB lights** in the middle.
6. Pick a color using the wheel, presets, or the **Hex** input on the right.
7. Click **Apply Colors To Selection** if needed. The color may update immediately when the LED selection is active.

Example: purple is `#A000FF`, or R 160, G 0, B 255.

Avoid **Apply All Devices** unless you deliberately want to change every connected OpenRGB device.

## 4. Independent LED slots, beacon, and notifications

The v0.2 plugin displays **HID slot 1** through **HID slot 15** in the **Devices** tab. Select a slot and set a color. Protocol slots are independently addressable in the outgoing USB report, but their mapping to physical mouse LED locations must be verified.

In **Settings → Bloody P93**:

1. Check **Enable RGB control**.
2. Click **Identify next LED slot (yellow)** repeatedly. Each click illuminates the next protocol slot, 1 through 15. Record which physical light responds (some slots may map to the same light or have no visible LED).
3. Enter comma-separated **Beacon group A** and **Beacon group B** slot numbers. The default split is `1,2,3,4,5,6,7` versus `8,9,10,11,12,13,14,15`. Adjust it to match your observed **physical left and right** groups.
4. Set **Beacon interval** (120–2000 ms). Check **Flashing beacon** to alternate yellow light between the two groups. Uncheck it to stop, then use **Restore selected OpenRGB colors**.
5. For external events, check **Enable local notification commands**. This enables a listener at `127.0.0.1:45893`, **only while you opt in**.

From the project's root directory, run:

```powershell
.\Send-P93Notification.ps1 -Event ALERT    # Yellow alternating, 5 seconds
.\Send-P93Notification.ps1 -Event ERROR    # Red alternating, 5 seconds
.\Send-P93Notification.ps1 -Event SUCCESS  # Green for 1.8 seconds
.\Send-P93Notification.ps1 -Event STOP     # Restore selected color slots
```

These scripts require local OpenRGB and the plugin; they do not access the internet. To integrate **ntfy**, a local agent or notification script must call the PowerShell sender when an ntfy message arrives. ChatGPT does not directly emit a Windows event when a response completes. [Full protocol and command specification](HID_PROTOCOL.md).

## 5. Modes, profiles, and limitations

- **Direct** mode remains the primary OpenRGB hardware mode. It now exposes 15 HID color slots separately. Their precise mapping to physical LED locations is not yet validated.
- **Speed** and **Brightness** controls on OpenRGB's native Direct device mode are unavailable; the plugin provides a separate **Beacon interval** control for the alternating software effect.
- **Saving Not Supported** means no hardware profile saving is implemented. OpenRGB's **Save Profile** concerns OpenRGB software profiles.
- Unchecking **Enable RGB control** prevents further writes but **does not automatically restore the previous color**. If necessary, restore lighting with a saved Bloody WorkShop 8 profile.
- Avoid competing lighting changes from Bloody WorkShop 8 while using OpenRGB. Saved button macros remain untouched by this plugin, though persistent configuration should still be checked after restarts.

## 6. Quick acceptance test

- [ ] The plugin's Settings page reports the P93 mouse as connected.
- [ ] Enabling RGB control allows changing from purple (`A000FF`) to red (`FF0000`) and back.
- [ ] Mouse left/right buttons, wheel, and existing screenshot macro continue working.
- [ ] Disabling the plugin stops sending RGB updates.
- [ ] Enabling the plugin after restarting OpenRGB still works.
- [ ] Optionally check after a Windows reboot.

**Real-world test, 10 Nov 2026:** device owner confirmed OpenRGB displays the P93, changes color through the GUI, and mouse buttons continue working. The **v0.2 per-slot and beacon features still need a dedicated physical test**, as do restart/reconnect scenarios.

## 7. Troubleshooting

| Issue | Suggested check |
| --- | --- |
| Plugin missing in Settings | Confirm the DLL is in `%APPDATA%\OpenRGB\plugins\`; fully exit and restart OpenRGB 1.1 |
| P93 missing from Devices | Check the exact P93 identity `09DA:31DE` and use **Retry device detection** |
| Color selector has no effect | Check **Enable RGB control**, select the colored LED square, then apply the color to the selection |
| Color is overwritten | Another utility, such as Bloody WorkShop 8, may also be controlling RGB lighting |
| PawnIO / I2C warning | PawnIO is not required for this mouse's Windows HID interface; ignore the warning for this device |
| Windows blocks the DLL | Verify release origin and checksum. Do not disable system-wide Smart App Control merely to install a plugin |
| Wrong color persists | Disable the plugin, then restore the saved lighting profile using Bloody WorkShop 8 |
| Mouse stops responding | Exit OpenRGB, reconnect the mouse; remove the plugin and report the issue if necessary |

Logs: `%APPDATA%\OpenRGB\logs\`. Avoid uploading raw USB traffic logs, which may include unrelated sensitive data.

## 8. Uninstallation

1. Exit OpenRGB completely.
2. Remove only `%APPDATA%\OpenRGB\plugins\OpenRGBBloodyP93Plugin.dll` (or remove the plugin in Settings).
3. Restart OpenRGB.
4. Restore the previous lighting from your saved Bloody WorkShop 8 profile if desired. The plugin does not alter button mappings.

## 9. Development and support

See the [repository](https://github.com/liikane/openrgb-bloody-p93) for sources, Windows CI builds and releases. The plugin uses OpenRGB 1.1 Plugin API v5, Qt 6.8.3, and 64-byte Windows HID Feature reports.

Report issues through [GitHub Issues](https://github.com/liikane/openrgb-bloody-p93/issues). Do not attempt arbitrary HID or firmware writes. License: GPL-2.0-or-later.
