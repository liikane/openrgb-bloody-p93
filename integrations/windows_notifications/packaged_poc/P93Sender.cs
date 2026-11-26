using System;
using System.Net.Sockets;
using System.Text;

namespace WindowsNotificationPoc
{
    internal sealed class P93Sender
    {
        private bool _enabled;

        internal void SetEnabled(bool enabled)
        {
            _enabled = enabled;
        }

        internal void Send(NotificationEvent notificationEvent)
        {
            if (!_enabled)
                return;

            var payload = Encoding.ASCII.GetBytes("P93:" + notificationEvent.Kind);
            using (var socket = new UdpClient())
                socket.Send(payload, payload.Length, "127.0.0.1", 45893);
        }
    }
}
