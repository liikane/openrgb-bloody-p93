# ntfy + Windows Event Log bridge — validation

**Test date:** 2026-11-10.
**Computer:** LAURIDELL, Windows, OpenRGB 1.1, Bloody P93, True Mouse Art v0.4.0.
**Implementation:** Python 3 standard library + Win32 `EvtSubscribe` (via ctypes), opt-in localhost UDP into existing OpenRGB plugin.

## Verified end-to-end ntfy -> mouse

1. Existing ntfy settings found at `Portable/Automation/Summary/settings.json`. The secret private topic was **not copied into the GitHub repository**.
2. HTTPS subscriber permission tested with HTTP **200** against the existing topic.
3. OpenRGB restarted with `rgbEnabled=true` and `notificationsEnabled=true`, localhost listener `127.0.0.1:45893` confirmed.
4. Bridge launched headlessly via `pythonw.exe`; log confirms JSON stream connected and four Windows event-log subscriptions active.
5. One test alert was **posted to the user's existing ntfy channel** using `Send-Ntfy.ps1` (HTTP 200), with `Priority:4`, `Tags:warning`.
6. Bridge log recorded `Sent local P93 event=ALERT source=ntfy`.
7. The P93 mouse's **read-only HID feature response** changed repeatedly between **two purple RGB slots `FF 00 FF`** and **six blue slots `00 00 FF`** during ~5 seconds of the alert. Seven unused HID fields remained dark. The event ended and output returned to black. This verifies a full ntfy -> bridge -> OpenRGB -> physical-device HID report chain, without modifying mouse macros.
8. Bridge uses one `pythonw` background process, not a constantly looping PowerShell window.

## Windows events (subscriptions accepted, events not forced)

Native `EvtSubscribe` returned valid subscriptions for:
- Microsoft Defender / Operational **1116** => ERROR
- Microsoft Defender / Operational **1117** => ALERT
- Windows Update Client / Operational **19** => SUCCESS
- Windows Update Client / Operational **20** => ERROR

The four event subscriptions are **active for future events** and don't read event descriptions. These are Event Log system events, **not the full Windows Toast notification center**. No malware/Windows Update failures were induced for testing.

## Launch and controls

- Current startup mechanism: **per-user Windows Task Scheduler**, task name `True Mouse Art Notification Bridge`, triggered at interactive Windows logon.
- Task may run without administrator rights and uses `pythonw.exe` with a single-instance Windows mutex.
- Install/uninstall controls are in the integration's `Install-BridgeTask.ps1` and `Uninstall-BridgeTask.ps1`.
- Diagnostic log: `Portable/Automation/OpenRGB-Ntfy-Bridge/bridge.log`, rotating, no topic/notification content in it.
- No new NTFY topic, third-party account, or paid service created.

## Next
- [ ] Test one real Windows Update completion/failure or Microsoft Defender alert when it naturally occurs.
- [ ] Add a separate privacy/permission-aware packaged Windows Toast listener for user-selected applications (see issue #5).
- [ ] Provide tray settings and event allowlist/quiet hours in standalone Vilgutaja (issues #6-#8).
- [ ] Consider application-specific ntfy rules if the existing topic triggers too many flashing notices.

## Startup task reliability follow-up

The scheduled task was installed under the current Windows user and launched a single pythonw background process when manually triggered. During an additional launch test, an ntfy JSON stream connected but did not deliver some subsequently published messages. A fallback `poll=1&since=...` worker was therefore added at ~12-second intervals, with message-ID deduplication and a 2-minute freshness cutoff. Pending final scheduled-task end-to-end validation for this updated version.

## Final bridge restart check — 10 November 2026

- Windows Task Scheduler **True Mouse Art Notification Bridge** successfully launched a single background `pythonw.exe` instance for the logged-in user. The process was observed running; its first ntfy connection was delayed on LAURIDELL and some alerts were dispatched late.
- A **12-second cached-message fallback** was therefore added alongside the original ntfy JSON stream. Stream and fallback share a 400-ID deduplication buffer and ignore messages older than 120 seconds. The message handling and stale-event suppression logic passed a new Python unit test.
- The current v0.2 bridge build was restarted manually while the per-user logon task remains registered for future login sessions. It connected to ntfy and registered all four Windows event subscriptions.
- A low-priority test message with explicit `p93_alert` tag was published to the existing ntfy channel (HTTP 200); the bridge reported `Sent local P93 event=ALERT source=ntfy-stream` at **15:27:34** local time. No duplicate dispatch was observed in the test window.
- A previous normal-priority ntfy test confirmed the actual P93 mouse color response via read-only HID reports.
- The complete Windows notification center/Toast collector is still separate future work requiring user permission. The native event-log subscriptions and ntfy bridge do not read arbitrary toast content.
