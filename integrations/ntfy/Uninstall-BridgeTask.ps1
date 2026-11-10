# Remove the per-user logon task and stop only this bridge process.
param([switch]$KeepRunning)
$ErrorActionPreference = 'Stop'
$taskName = 'True Mouse Art Notification Bridge'
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Output "Removed per-user task: $taskName"
} else {
    Write-Output "Task was not installed."
}
if (-not $KeepRunning) {
    $script = Join-Path $PSScriptRoot 'bridge.py'
    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq 'pythonw.exe' -and $_.CommandLine -and $_.CommandLine.Contains($script)
    }
    foreach ($process in $processes) {
        Stop-Process -Id $process.ProcessId -ErrorAction Stop
        Write-Output ("Stopped bridge PID " + $process.ProcessId)
    }
}
