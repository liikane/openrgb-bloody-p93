# Sends a local RGB notification to the Bloody P93 OpenRGB plugin.
# Requires: OpenRGB 1.1, P93 plugin v0.2+, both RGB and local notifications enabled.
# No internet, no global hooks, no HID device modification from this script.
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('ALERT','ERROR','NOTICE','SUCCESS','STOP')]
    [string]$Event
)
$ErrorActionPreference = 'Stop'
$message = 'P93:' + $Event.ToUpperInvariant()
$udp = [System.Net.Sockets.UdpClient]::new()
try {
    $payload = [System.Text.Encoding]::ASCII.GetBytes($message)
    [void]$udp.Send($payload,$payload.Length,'127.0.0.1',45893)
    Write-Output "Local P93 notification sent: $Event"
} finally {
    $udp.Dispose()
}
