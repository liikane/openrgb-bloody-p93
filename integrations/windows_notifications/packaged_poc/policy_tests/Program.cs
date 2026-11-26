using WindowsNotificationPoc;

var policy = new NotificationPolicy();
policy.Initialize(Array.Empty<ToastId>());
var old = new ToastId("mail.app", 1);
if (policy.ProcessSnapshot(new[] { old }).Count != 0)
    throw new Exception("The empty allowlist must suppress events.");

policy.SetRules(new Dictionary<string, EventKind>
{
    ["mail.app"] = EventKind.ALERT
});
if (policy.ProcessSnapshot(new[] { old }).Count != 0)
    throw new Exception("Previously seen Toasts must not be replayed.");

var fresh = new ToastId("mail.app", 2);
var events = policy.ProcessSnapshot(new[] { fresh, fresh });
if (events.Count != 1 || events[0].Kind != EventKind.ALERT)
    throw new Exception("Only one configured classification should be produced.");

policy.SetRules(new Dictionary<string, EventKind>());
if (policy.ProcessSnapshot(new[] { new ToastId("mail.app", 3) }).Count != 0)
    throw new Exception("Removing an app from the allowlist must suppress future events.");

Console.WriteLine("Packaged POC notification policy tests passed.");
