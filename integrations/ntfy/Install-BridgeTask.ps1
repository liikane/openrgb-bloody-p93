# Install True Mouse Art bridge as a per-user Windows logon task.
# No elevation or service required. No changes to Smart App Control.
param([switch]$StartNow)
$ErrorActionPreference = 'Stop'
$taskName = 'True Mouse Art Notification Bridge'
$script = Join-Path $PSScriptRoot 'bridge.py'
$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source)
if (-not $pythonw) {
    $python = (Get-Command python.exe -ErrorAction Stop).Source
    $pythonw = Join-Path (Split-Path $python) 'pythonw.exe'
}
if (!(Test-Path -LiteralPath $pythonw)) { throw 'pythonw.exe not found' }
if (!(Test-Path -LiteralPath $script)) { throw 'bridge.py not found' }

$python = Join-Path (Split-Path $pythonw) 'python.exe'
& $python $script --check
if ($LASTEXITCODE -ne 0) { throw 'Bridge check failed, task not installed' }

$account = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute $pythonw -Argument ('"' + $script + '"') -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $account
$principal = New-ScheduledTaskPrincipal -UserId $account -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'True Mouse Art: ntfy and selected Windows events to local OpenRGB RGB notifications' -Force | Out-Null
Write-Output "Installed per-user task: $taskName"
Write-Output "Log: $HOME\Portable\Automation\OpenRGB-Ntfy-Bridge\bridge.log"
if ($StartNow) {
    Start-ScheduledTask -TaskName $taskName
    Write-Output "Scheduled task start requested (only one instance is allowed)."
}
