using System;
using System.Collections.Generic;
using System.Linq;

namespace WindowsNotificationPoc
{
    internal enum EventKind
    {
        ALERT,
        ERROR,
        SUCCESS,
        NOTICE
    }

    internal sealed class NotificationEvent
    {
        internal EventKind Kind { get; private set; }

        internal NotificationEvent(EventKind kind)
        {
            Kind = kind;
        }
    }

    internal sealed class ToastId : IEquatable<ToastId>
    {
        internal string AppId { get; private set; }
        internal uint Id { get; private set; }

        internal ToastId(string appId, uint id)
        {
            if (string.IsNullOrWhiteSpace(appId))
                throw new ArgumentException("App identity must be non-empty.", nameof(appId));
            AppId = appId;
            Id = id;
        }

        public bool Equals(ToastId other)
        {
            return other != null && Id == other.Id
                && StringComparer.Ordinal.Equals(AppId, other.AppId);
        }

        public override bool Equals(object obj)
        {
            return Equals(obj as ToastId);
        }

        public override int GetHashCode()
        {
            unchecked
            {
                return (StringComparer.Ordinal.GetHashCode(AppId) * 397) ^ (int)Id;
            }
        }
    }

    internal sealed class NotificationPolicy
    {
        private const int MaxSeen = 100000;
        private Dictionary<string, EventKind> _rules =
            new Dictionary<string, EventKind>(StringComparer.Ordinal);
        private HashSet<ToastId> _seen = new HashSet<ToastId>();
        private bool _initialized;

        internal void SetRules(IDictionary<string, EventKind> rules)
        {
            _rules = new Dictionary<string, EventKind>(rules, StringComparer.Ordinal);
        }

        internal void Initialize(IEnumerable<ToastId> notifications)
        {
            if (_initialized)
                throw new InvalidOperationException("Notification baseline already initialized.");
            var baseline = ValidateSnapshot(notifications);
            _seen = baseline;
            _initialized = true;
        }

        internal List<NotificationEvent> ProcessSnapshot(IEnumerable<ToastId> notifications)
        {
            if (!_initialized)
                throw new InvalidOperationException("Initialize the startup baseline first.");
            var snapshot = ValidateSnapshot(notifications);
            var added = snapshot.Except(_seen).ToList();
            if (_seen.Count + added.Count > MaxSeen)
                throw new InvalidOperationException("Notification session limit reached.");
            foreach (var item in added)
                _seen.Add(item);

            return added
                .Where(item => _rules.ContainsKey(item.AppId))
                .OrderBy(item => item.AppId, StringComparer.Ordinal)
                .ThenBy(item => item.Id)
                .Select(item => new NotificationEvent(_rules[item.AppId]))
                .ToList();
        }

        private static HashSet<ToastId> ValidateSnapshot(IEnumerable<ToastId> notifications)
        {
            var snapshot = new HashSet<ToastId>(notifications);
            if (snapshot.Count > MaxSeen)
                throw new InvalidOperationException("Notification snapshot exceeds the session limit.");
            return snapshot;
        }
    }
}
