# True Mouse Art — Bloody P93 LED / HID map

**Eight physical LEDs, eight visible OpenRGB controls, fifteen fields in the HID report.** This mapping was identified by the P93 owner on 10 November 2026. The illustration is a schematic, not a photograph or a dimensionally exact hardware drawing.

![Top-view diagram with eight numbered LED locations on a stylized Bloody P93 mouse](mouse-led-map.svg)

## LED-to-slot-to-byte mapping

Each visible LED is numbered identically to its corresponding 1-based HID RGB slot. Every slot occupies three bytes **R, G, B** in the 64-byte HID Feature report.

| LED | HID slot | Location (English) | Asukoht (eesti keeles) | R offset | G offset | B offset |
|---:|---:|---|---|---:|---:|---:|
| **1** | 1 | Wheel / middle button | Rullik / keskmine klahv | **8** | 9 | 10 |
| **2** | 2 | Left front | Vasak ees | **11** | 12 | 13 |
| **3** | 3 | Right front | Parem ees | **14** | 15 | 16 |
| **4** | 4 | Middle, beneath three extra buttons | Kolme lisanupu all keskel | **17** | 18 | 19 |
| **5** | 5 | Right middle | Parem keskel | **20** | 21 | 22 |
| **6** | 6 | Left middle | Vasak keskel | **23** | 24 | 25 |
| **7** | 7 | Left rear; contributes to logo lighting | Vasak taga, valgustab ka logo | **26** | 27 | 28 |
| **8** | 8 | Right rear / center; contributes to logo lighting | Parem taga ja keskel, valgustab ka logo | **29** | 30 | 31 |

**Logo:** the prominently visible mouse logo is illuminated by **LEDs 7 and 8 together**. The bright wheel (LED **1**) is particularly useful for notifications.

**HID slots 9–15 do not correspond to physical P93 LEDs.** They are hidden from OpenRGB's Devices panel. Nevertheless, the underlying vendor HID packet remains exactly **64 bytes** and still provides fifteen RGB triplet *positions*; slots 9–15 remain zero in new color reports. No protocol truncation occurs.

### Feature report structure

`[07 03 06 02] [00 00 00 00] [LED1:R,G,B] [LED2:R,G,B] ... [LED8:R,G,B] [00 × 21] [00 × 11]`

- Bytes 0–3: command prefix / report ID `07 03 06 02`.
- Bytes 4–7: four zero/reserved bytes.
- Bytes 8–31: physical LEDs 1–8, eight RGB triples.
- Bytes 32–52: seven unused RGB triples (slots 9–15), **all zero**.
- Bytes 53–63: eleven reserved bytes, **all zero**.

The initialization reports (`07 03 06 01` and `07 03 06 00` with byte 8 set to 1) are documented in [HID_PROTOCOL.md](HID_PROTOCOL.md).

## Beacon / vilkur

For the first operationally useful attention pattern, the mouse alternates two groups rather than merely switching all lights on/off:

| Phase | Yellow `#FFD200` | Off |
|---|---|---|
| **A** | **1 + 4** (wheel + extra-button area) | 2, 3, 5, 6, 7, 8 |
| **B** | **2 + 3 + 5 + 6 + 7 + 8** (outer lights + logo) | 1, 4 |

This is a **center-versus-perimeter beacon**, *not* a claim that the two phases correspond to the physical left/right halves. The interval is adjustable in the plugin. The group inputs remain editable for future alternative patterns.

## RGB color examples

| Use | Color | Hex | R,G,B |
|---|---|---|---|
| Flashing warning | Yellow | `#FFD200` | 255,210,0 |
| Error / urgent action | Red | `#FF0000` | 255,0,0 |
| Completed task | Green | `#00FF00` | 0,255,0 |
| Idle / decorative | Purple | `#A000FF` | 160,0,255 |
| Off | Black | `#000000` | 0,0,0 |

The same protocol could be used by a different program, but **do not send arbitrary vendor commands**; the other command families may affect stored settings. The supplied plugin implements only the RGB commands identified through physical testing.

*Hardware mapping: reported by the P93 owner, 10 November 2026. Illustrative top view: vector original by the project, no third-party product image.*
