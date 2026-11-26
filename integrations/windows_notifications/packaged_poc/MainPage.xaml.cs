using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Windows.ApplicationModel;
using Windows.UI.Core;
using Windows.UI.Notifications;
using Windows.UI.Notifications.Management;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;

namespace WindowsNotificationPoc
{
    public sealed partial class MainPage : Page
    {
        private readonly NotificationPolicy _policy = new NotificationPolicy();
        private readonly SemaphoreSlim _snapshotLock = new SemaphoreSlim(1, 1);
        private readonly P93Sender _sender = new P93Sender();
        private bool _initialized;
        private bool _forwarding;
        private bool _snapshotPending;

        public MainPage()
        {
            InitializeComponent();
        }

        private async void RequestAccessButton_Click(object sender, RoutedEventArgs e)
        {
            RequestAccessButton.IsEnabled = false;
            var listener = UserNotificationListener.Current;
            UserNotificationListenerAccessStatus access;
            try
            {
                access = await listener.RequestAccessAsync();
            }
            catch
            {
                StatusText.Text = "Access request failed. Forwarding remains disabled.";
                return;
            }

            if (access != UserNotificationListenerAccessStatus.Allowed)
            {
                StatusText.Text = "Access was not granted. Change it in Windows Settings and restart this app.";
                return;
            }

            var reconcilePending = false;
            await _snapshotLock.WaitAsync();
            try
            {
                listener.NotificationChanged += Listener_NotificationChanged;
                var notifications = await listener.GetNotificationsAsync(NotificationKinds.Toast);
                var metadata = ToMetadata(notifications);
                _policy.Initialize(metadata);
                _initialized = true;
                UpdateAppChoices(metadata.Select(item => item.AppId));
                reconcilePending = _snapshotPending;
                _snapshotPending = false;
                ApplyRulesButton.IsEnabled = true;
                ForwardingButton.IsEnabled = true;
                StatusText.Text = "Access granted. Allowlist empty; forwarding disabled.";
            }
            catch
            {
                StatusText.Text = "Could not initialize the notification baseline. Forwarding remains disabled.";
            }
            finally
            {
                _snapshotLock.Release();
            }
            if (reconcilePending)
                await ReconcileSnapshotAsync();
        }

        private async void Listener_NotificationChanged(
            UserNotificationListener sender, NotificationChangedEventArgs args)
        {
            await Dispatcher.RunAsync(CoreDispatcherPriority.Normal, () =>
            {
                if (_initialized)
                    _ = ReconcileSnapshotAsync();
                else
                    _snapshotPending = true;
            });
        }

        private async Task ReconcileSnapshotAsync()
        {
            if (!_initialized)
                return;

            await _snapshotLock.WaitAsync();
            try
            {
                if (UserNotificationListener.Current.GetAccessStatus()
                    != UserNotificationListenerAccessStatus.Allowed)
                {
                    SetForwarding(false);
                    StatusText.Text = "Access revoked. Forwarding disabled.";
                    return;
                }

                var notifications = await UserNotificationListener.Current
                    .GetNotificationsAsync(NotificationKinds.Toast);
                var metadata = ToMetadata(notifications);
                var events = _policy.ProcessSnapshot(metadata);
                UpdateAppChoices(metadata.Select(item => item.AppId));
                foreach (var notificationEvent in events)
                {
                    if (_forwarding)
                        _sender.Send(notificationEvent);
                }
            }
            catch
            {
                SetForwarding(false);
                StatusText.Text = "Notification processing failed. Forwarding disabled.";
            }
            finally
            {
                _snapshotLock.Release();
            }
        }

        private static List<ToastId> ToMetadata(
            IReadOnlyList<UserNotification> notifications)
        {
            var result = new List<ToastId>();
            foreach (var notification in notifications)
            {
                var appInfo = notification.AppInfo;
                if (appInfo != null && !string.IsNullOrWhiteSpace(appInfo.Id))
                    result.Add(new ToastId(appInfo.Id, notification.Id));
            }
            return result;
        }

        private void UpdateAppChoices(IEnumerable<string> appIds)
        {
            var ids = appIds.Distinct(StringComparer.Ordinal).OrderBy(id => id, StringComparer.Ordinal);
            var existing = AppChoices.Children.OfType<StackPanel>()
                .ToDictionary(row => (string)row.Tag, StringComparer.Ordinal);
            foreach (var appId in ids)
            {
                if (existing.ContainsKey(appId))
                    continue;

                var row = new StackPanel { Orientation = Orientation.Horizontal, Tag = appId, Spacing = 8 };
                row.Children.Add(new CheckBox { Content = appId });
                var kindPicker = new ComboBox { Width = 140, SelectedIndex = 0 };
                kindPicker.Items.Add(new ComboBoxItem { Content = "ALERT" });
                kindPicker.Items.Add(new ComboBoxItem { Content = "ERROR" });
                kindPicker.Items.Add(new ComboBoxItem { Content = "SUCCESS" });
                kindPicker.Items.Add(new ComboBoxItem { Content = "NOTICE" });
                row.Children.Add(kindPicker);
                AppChoices.Children.Add(row);
            }
        }

        private void ApplyRulesButton_Click(object sender, RoutedEventArgs e)
        {
            var rules = new Dictionary<string, EventKind>(StringComparer.Ordinal);
            foreach (var row in AppChoices.Children.OfType<StackPanel>())
            {
                var checkBox = (CheckBox)row.Children[0];
                if (checkBox.IsChecked != true)
                    continue;

                var picker = (ComboBox)row.Children[1];
                var selected = (ComboBoxItem)picker.SelectedItem;
                rules[(string)row.Tag] = (EventKind)Enum.Parse(typeof(EventKind), (string)selected.Content);
            }
            _policy.SetRules(rules);
            StatusText.Text = rules.Count == 0
                ? "Allowlist empty. Forwarding remains disabled until enabled."
                : "Allowlist updated in memory.";
        }

        private void ForwardingButton_Click(object sender, RoutedEventArgs e)
        {
            SetForwarding(!_forwarding);
            StatusText.Text = _forwarding
                ? "Forwarding enabled for new allowlisted Toasts."
                : "Forwarding disabled.";
        }

        private void SetForwarding(bool enabled)
        {
            _forwarding = enabled;
            _sender.SetEnabled(enabled);
            ForwardingButton.Content = enabled ? "Disable event forwarding" : "Enable event forwarding";
        }
    }
}
