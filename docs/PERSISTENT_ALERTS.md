# True Mouse Art — persistent alerts and always-on RGB (v0.5)

**Eesti keeles:** Hiir jääb vilkuma, kuni kasutaja teate kinnitab.
**English:** The mouse is your attention beacon, not a five-second distraction.

## How it works / Kuidas töötab

If a message arrives while you are away, the P93 **keeps displaying it until you acknowledge the pending events**. The plugin stores just the event categories (not message bodies), so pending alerts can resume after OpenRGB restarts.

### Alert patterns / Teavitusmustrid

| Sündmus | Group A: LED 1 + 4 | Group B: LED 2 + 3 + 5 + 6 + 7 + 8 | Tähendus |
|---|---|---|---|
| `ERROR` | Red / punane | Yellow / kollane | Viga, vajab kontrolli |
| `ALERT` | Red / punane | Blue / sinine | Tähelepanu |
| `SUCCESS` | Green / roheline | White / valge | Töö sai valmis |
| `NOTICE` | Green / roheline | Yellow / kollane | Tavaline teavitus |

The group colors above are *notification defaults*. The existing **Group A / B color dialogs** still configure manual beacons independently.

**Two pending notifications:** display two full A/B cycles of the first, then two cycles of the next, and repeat. Up to 16 event categories are retained in the queue. Duplicate types are also counted; the oldest entry is dropped if the queue is full. Nothing auto-acknowledges on timeout.

### How to acknowledge / Kuidas kinnitada

- OpenRGB → **Settings → Bloody P93 → Acknowledge all alerts and resume colorful idle**.
- Global keyboard shortcut: **Ctrl + Shift + F12**. Requires the included local ntfy bridge running (it uses Windows `RegisterHotKey`, not a keyboard hook or keylogger).
- Command line: `Send-P93Notification.ps1 -Event ACK` — `STOP` is also supported as an acknowledgement for compatibility.

The acknowledgement removes all queued notifications and starts the nonblack eight-LED color cycle.

### Idle / tavaolek

When the alert queue is empty, **all eight physical LEDs rotate through eight muted colors** (red/purple, gold, green, cyan, blue...). The pattern advances by one LED every **550 ms** by default; the speed is adjustable **250–2000 ms** under `Color rotation speed`.

The **Idle lighting** checkbox can disable animation deliberately. If disabled, OpenRGB-selected device colors are shown instead (which could be black if previously configured that way). Idle lighting is enabled by default to prevent the mouse going dark after alerts.

The plugin saves `pendingEvents`, `idleAnimation` and `idleIntervalMs` per user with Qt QSettings. It does not alter firmware or mouse macros.

### Accessibility and safety

- The persistent alert beacon has a minimum **500 ms** per phase (even if the manual interval is set lower), avoiding high-frequency strobing.
- The user can disable RGB control, and the acknowledgement shortcut is deliberate rather than tracking every key press.
- Notifications are held by category only; no private message content is saved.
- When the system is locked/asleep and OpenRGB is not running, hardware writes cannot occur. NTFY server cache or other upstream delivery is still subject to its own retention limits; alerts only become persistent once **the running plugin receives them**.

## Test procedure

1. Enable **RGB control** and **local notification commands** under Bloody P93 plugin settings.
2. Send `ERROR`, then `SUCCESS` from ntfy or the local PowerShell sender.
3. Watch the two distinct color combinations alternate for at least 20 seconds.
4. Press **Ctrl + Shift + F12**. Alerts should stop and all eight lights should rotate colors instead of turning black.
5. Send another alert and restart OpenRGB. Alert should reappear because the pending categories are saved.
6. Verify screenshot and mouse button macros still function normally.

This extension is a community beta until the new state machine is checked on a physical P93.
