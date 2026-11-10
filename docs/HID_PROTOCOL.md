# True Mouse Art — Bloody P93 HID RGB protocol

A documented community-derived implementation of RGB control for the **Bloody P93** mouse. It is **not** an official manufacturer's protocol specification. The device owner mapped the LED positions physically on 10 November 2026; packet format was verified using the Windows HID API and prior actual RGB color changes.

## 1. Target and boundaries

| Parameter | Value |
|---|---|
| Model | Bloody P93 |
| USB VID / PID | `0x09DA / 0x31DE` |
| HID collection | `MI_02 / COL04` |
| Usage page / usage | `0xFF32 / 0x0218` |
| Feature report | **ID 0x07**, exactly **64 bytes** |
| Transport | Windows HID `HidD_SetFeature`; no custom driver |
| Native HID RGB fields | **15 RGB triplets** in the report |
| Actual physical RGB LEDs | **8** |
| Implemented/visible LEDs | **1–8**; report triplets **9–15 are zero-filled** |

Before writing, the plugin checks the exact device ID, collection, HID usage, report length, and response prefix. It does not send DPI, macro, button, bootloader or firmware instructions.

## 2. Commands

All commands are 64-byte buffers. Byte positions use **zero-based offsets**.

### Initialize RGB

```text
Offset  00 01 02 03 04 05 06 07 08 ...
Values  07 03 06 01 00 00 00 00 00 ... zero up to 63
```

Enter RGB control mode, once upon device connection or when direct mode needs reinitialization.

### Enable Direct control

```text
Offset  00 01 02 03 04 05 06 07 08 09 ...
Values  07 03 06 00 00 00 00 00 01 00 ... zero up to 63
```

### Set RGB colors

```text
Offset  00 01 02 03 04 05 06 07 08 09 10 11 12 13 ... 29 30 31 32 ... 52 53 ... 63
Values  07 03 06 02 00 00 00 00 R1 G1 B1 R2 G2 B2 ... R8 G8 B8 00 ... 00 00 ... 00
```

- **Bytes 0–3:** `07 03 06 02` — report ID and RGB-color command.
- **Bytes 4–7:** four zero/reserved bytes.
- **Bytes 8–31:** eight 3-byte RGB colors for **physical LEDs 1–8**.
- **Bytes 32–52:** seven more RGB fields in the *protocol*, but these are **unused by this P93** and remain all zero.
- **Bytes 53–63:** eleven zero/reserved bytes.

For example, for **LED 1 purple**, set bytes 8,9,10 to `A0 00 FF` (160,0,255). For **LED 4 yellow**, set bytes 17,18,19 to `FF D2 00` (255,210,0). All other bytes keep their defined values.

## 3. Physical LED = SLOT = HID byte map

![Bloody P93 top-view LED schematic](mouse-led-map.svg)

| Physical LED | SLOT (1-based) | Location | R byte | G byte | B byte |
|---:|---:|---|---:|---:|---:|
| 1 | 1 | Wheel / middle button | 8 | 9 | 10 |
| 2 | 2 | Left front | 11 | 12 | 13 |
| 3 | 3 | Right front | 14 | 15 | 16 |
| 4 | 4 | Middle, under 3 extra buttons | 17 | 18 | 19 |
| 5 | 5 | Right middle | 20 | 21 | 22 |
| 6 | 6 | Left middle | 23 | 24 | 25 |
| 7 | 7 | Left rear, shared logo lighting | 26 | 27 | 28 |
| 8 | 8 | Right rear / center, shared logo lighting | 29 | 30 | 31 |

The mouse **logo illuminates through LEDs 7 and 8 together**. LED 1 (wheel) is especially prominent. Slots 9–15 have no physical LEDs and are not displayed as editable devices in OpenRGB.

See [LED_MAP.md](LED_MAP.md) for bilingual location names, examples and exact group assignments.

## 4. True Mouse Art — flashing beacon

The default beacon has two **complementary phases**, alternating every 320 ms initially:

| Phase | Lit yellow `FF D2 00` | Off |
|---|---|---|
| **A** | **1 + 4** (wheel and extra-button group) | 2, 3, 5, 6, 7, 8 |
| **B** | **2 + 3 + 5 + 6 + 7 + 8** | 1, 4 |

The plugin sends one normal color command per phase and changes these groups on a timer. This is **not** a left-right physical split; users may customize groups in the settings. The report still contains 15 fields, but each frame sets only the first eight.

The user can activate flashing manually from the OpenRGB plugin settings or via local `P93:ALERT` / `P93:ERROR` notifications. Previously verified HID patterns used an older 7/8-field grouping; the 1+4 versus six-LED grouping is an updated, separately tested configuration.

## 5. Local notification command interface

An optional, user-enabled local UDP socket on **127.0.0.1:45893** accepts these ASCII messages:

| Data | Effect |
|---|---|
| `P93:ALERT` / `P93:NOTICE` | Two groups flashing yellow for 5 s |
| `P93:ERROR` | Two groups flashing red for 5 s |
| `P93:SUCCESS` | Eight physical LEDs green for 1.8 s |
| `P93:STOP` | Stop and restore configured colors |

The listener is **off by default** unless explicitly enabled. It does not contact the internet, watch keyboard activity, or monitor ChatGPT. The repository includes `Send-P93Notification.ps1` for local script integrations.

## 6. Device notes, testing, and safety

- Real P93 hardware has already responded to purple static color, red/green flash, OpenRGB UI RGB changes and HID output queries. Prior notification testing verified that HID reports alternate as expected.
- C++ unit tests verify the **15-field transport with 8 usable LEDs** and the two-phase default grouping; physical LED locations are mapped by the user.
- No hardcoded commands outside `07 03 06 01`, `07 03 06 00`, `07 03 06 02` are used. **Do not guess additional vendor commands**; they might change stored profiles or firmware.
- The plugin uses Windows HID and WinSock APIs without PawnIO, USB capture drivers or other third-party kernel drivers.
- The user's Bloody WorkShop 8 button configuration is independent of this plugin. Running multiple RGB controllers simultaneously may create visual conflicts.
- Device mapping evidence is provided in [VALIDATION.md](VALIDATION.md). Source implementation: [P93Protocol.h](../src/P93Protocol.h) and [P93Hid.cpp](../src/P93Hid.cpp).

License: GPL-2.0-or-later. Independent community research, not a manufacturer-endorsed API.
