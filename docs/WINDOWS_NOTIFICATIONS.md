# Windows notification bridge / Windowsi teavituste sild

## Purpose

The **True Mouse Art** plugin already accepts small event commands locally and changes Bloody P93 RGB lighting. It **does not** read the Windows notification center. A **separate, opt-in, open-source notification bridge** is preferable to adding broad Windows notification permissions to a hardware-control plugin.

The bridge would observe **only user-selected applications** and forward **only event type** to the existing local plugin on `127.0.0.1:45893`. It must not transmit notification contents over the internet, store messages or introduce keyboard hooks.

## Recommended design: separate lightweight Windows tray app

```mermaid
flowchart LR
    A["Windows Toast notifications"] --> B["UserNotificationListener"]
    B --> C["Allowlist + deduplication + rules"]
    C --> D["Loopback UDP 127.0.0.1:45893"]
    D --> E["True Mouse Art OpenRGB plugin"]
    E --> F["P93: 8 RGB LEDs"]
```

Microsoft's documented API: [UserNotificationListener](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/notification-listener).

### What it needs

1. A **packaged Windows application** with the `userNotificationListener` capability declared in the app package manifest, or another supported application identity. A plain unpackaged executable **may not receive notification events reliably** — see [Windows App SDK issue #6172](https://github.com/microsoft/WindowsAppSDK/issues/6172).
2. The user's **explicit permission** granted by `UserNotificationListener.Current.RequestAccessAsync()` from the UI thread.
3. An explicit **app allowlist**: e.g. Windows Security, Outlook, ntfy, a chosen local automation program. Default is **no apps selected**.
4. Event handling: `NotificationChanged` or the supported background trigger, plus `GetNotificationsAsync(NotificationKinds.Toast)` for app identities and notification IDs. Only newly added items are acted on; old notifications are not replayed after app restart.
5. Local classifications, without storing content: `ERROR` -> `P93:ERROR`, `WARNING` -> `P93:ALERT`, `COMPLETED` -> `P93:SUCCESS`. Ordinary unclassified notices may be ignored or mapped to `P93:NOTICE`.
6. A privacy-first tray UI with **Pause**, **Stop**, **Allowed apps**, and **Test red/green/yellow**. Prevent repeat signals, limit how many times one notification triggers the mouse, and respect user-specified quiet hours.
7. An optional toggle to start only when the user logs in; no Windows service and no cloud account.

### Optional fast path for specific programs

If a program **already runs a script** when work completes, it can use `Send-P93Notification.ps1` directly. This is more reliable and simpler than inspecting Windows notifications. Examples include PowerShell automation, build scripts, agent wrappers, or an existing ntfy subscriber. Only use the full notification listener when the program does not have a native hook.

### Existing project for comparison

[WinToastRelay](https://github.com/RavelloH/WinToastRelay) implements a Windows notification listener forwarding messages to HTTP webhooks. It is useful for reviewing Windows notification API usage, but sending complete notifications to remote webhooks is not appropriate for True Mouse Art by default. The P93 plugin expects a minimal **UDP event code**, not an HTTP webhook or full notification text. It is possible to adapt or build a separate bridge without depending on a paid service.

### Security considerations

Notifications may contain personal email subjects, names, calendar details, one-time passwords, and other secrets. The proposed bridge should read only the app identity and notification metadata required for locally configured rules, avoid persistent logs, never forward raw text by default, and support disabling access at any time. Windows permission must be requested from the person using the computer; it cannot be granted silently by the plugin.

Users must not assume all Windows events appear as Toast notifications (some are native dialogs, tray changes, and application-only alerts). ChatGPT web completion is **not automatically available** through the notification API unless a separate desktop application emits a Windows Toast event.

## Packaged Windows proof of concept

[`integrations/windows_notifications/packaged_poc`](../integrations/windows_notifications/packaged_poc) is a minimal UWP package with the `userNotificationListener` capability. It does not start listening or ask for permission at launch. The user must click **Request notification access**; after consent, the app seeds a startup baseline and presents app identities seen in current Toast metadata. Its allowlist and event-kind rules are empty and kept in memory only. Forwarding has a separate, explicit **Enable event forwarding** action.

To build and run it on a Windows 10/11 development machine:

1. Install Visual Studio 2022 with the **Universal Windows Platform development** workload and Windows 10 SDK 10.0.19041.0 or later.
2. Open `integrations/windows_notifications/packaged_poc/WindowsNotificationPoc.csproj`, restore packages, and deploy from Visual Studio. For a distributable MSIX, create a local test signing certificate matching the manifest publisher (`CN=Liikane`) and sign the package; do not install a certificate or package unless you trust it.
3. Launch the app. Click **Request notification access** and respond to the Windows consent prompt. To revoke access later, use Windows Settings > Privacy & security > Notifications.
4. With access granted, select desired app identities and event classes, click **Apply allowlist**, then separately click **Enable event forwarding**. Disable forwarding or close the app to stop it. No hardware is needed to build or exercise the UI.
5. To receive effects, separately enable the P93 plugin's local command receiver. The app attempts to send only `P93:<kind>` to `127.0.0.1:45893`. UWP loopback network isolation can prevent a packaged app from reaching a desktop plugin; this prototype does not grant broad network capabilities or configure a loopback exemption. That transport limitation has not been validated on Windows.

The listener reads only `UserNotification.AppInfo.Id` and `UserNotification.Id`; it never inspects notification content or writes identities, IDs, event history, or rules to disk. The app's C# `NotificationPolicy` is a packaged adapter implementation of the same startup-baseline, explicit allowlist, in-memory deduplication, and event-only contract tested by the Python `NotificationPolicy` below. Both senders are disabled by default, and the C# sender hard-codes the loopback destination. No internet endpoint, telemetry, service, keyboard hook, or hardware write is implemented.

The repository's Windows workflow runs synthetic policy tests and attempts to compile/package the UWP PoC. No real notification access, consent UI, signed MSIX installation, loopback exemption/transport, P93 plugin behavior, or P93 hardware behavior has been tested by this cloud agent. Windows Toast and hardware validation remain separate manual checks.

## Offline policy core

[`integrations/windows_notifications/core.py`](../integrations/windows_notifications/core.py) is a standard-library-only foundation for the shared notification service, **not a listener, tray app, or installable package**. Nothing runs automatically or changes the plugin. Run its synthetic tests with:

```sh
python integrations/windows_notifications/test_core.py
```

The version 1 in-process event schema is `NotificationEvent(kind)`, where `kind` is one of `EventKind.ALERT`, `ERROR`, `SUCCESS`, or `NOTICE`. It contains no app ID, notification ID, title, body, or other content. A future acquisition layer supplies only `ToastId(app_id, notification_id)` values to `NotificationPolicy`; IDs are case-sensitive and notification IDs are unsigned 32-bit integers. `set_rules` replaces the initially empty allowlist with explicit app-ID-to-kind rules. Classification comes solely from those rules, never from notification text. The same events can be consumed by future OpenRGB Bridge or Vilgutaja adapters.

Call `initialize` once with a complete current Toast snapshot before processing subsequent complete snapshots with `process_snapshot`. Startup IDs and all seen IDs, including disallowed ones, are suppressed for the rest of the session; enabling an app later does not replay old Toasts. IDs are retained only in memory. If the session would exceed 100,000 distinct IDs, the policy fails closed; restart and establish a new baseline. A future listener must serialize or otherwise reconcile subscription and startup snapshot handling, including notifications arriving during startup, without replaying old notifications. It must keep feeding snapshots while paused so that resuming does not replay accumulated Toasts.

`P93Sender` starts disabled. A future UI must set it enabled only after explicit user opt-in and disable it on pause or revoke. It sends only `P93:<kind>` as ASCII to `127.0.0.1:45893`; no other destination is configurable. UDP does **not** reveal whether the plugin receiver is enabled or whether the device reacted. The user must separately enable the plugin receiver; a successful send is not a delivery confirmation. This sender has no queue or retry.

Still required before this is a verified Windows notification bridge:

- Build and deploy the packaged prototype on Windows with the required UWP workload; verify consent, denial/revocation, notification subscription, and AppContainer loopback behavior.
- On Windows 11, verify startup suppression and allowlisting with synthetic or real Toasts, then separately verify an allowed event reaches the P93 plugin. No real Toast listener or P93 hardware behavior has been validated by these synthetic tests.

## Current status

- [x] P93 plugin supports opt-in local commands `P93:ALERT`, `P93:NOTICE`, `P93:ERROR`, `P93:SUCCESS`, `P93:STOP`.
- [x] Standalone PowerShell sender available in repository.
- [x] Bridge architecture and privacy constraints documented.
- [x] Offline event policy and opt-in loopback sender covered by synthetic tests.
- [x] Add a separate packaged Windows proof-of-concept with listener capability, explicit consent UI, and empty in-memory allowlist.
- [x] Add metadata-only event policy and loopback sender in the packaged prototype with synthetic tests.
- [ ] Verify notification deduplication, filtering and classification on Windows 11.
- [ ] Demonstrate end-to-end Windows Toast -> local P93 RGB effect.

No standalone listener has yet been installed or enabled on LAURIDELL.

## Interim bridge shipped (10 November 2026)

A lightweight Python integration is available: [ntfy + Windows Event Log bridge](../integrations/ntfy/README.md). It subscribes to the user's ntfy JSON stream and **four specific future Windows Event Log events** using the native Windows EvtSubscribe API: Microsoft Defender IDs 1116/1117 and Windows Update IDs 19/20. Actual ntfy-to-P93 HID output was verified. It does **not** read generic Windows Toast messages; those require the separate opt-in packaged application described above.
