# Manage the optional Rhod 600 background RGB notification adapter.
# Only registers a per-user interactive logon task; no Windows service or privileges.
param(
    [ValidateSet("Install","Stop","Uninstall","Status")]
    [string]$Mode = "Status"
)
$ErrorActionPreference = 'Stop'
$name = 'True Mouse Art - Genesis Rhod 600'
$script = Join-Path $PSScriptRoot 'daemon.py'
$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source)
if (-not $pythonw) {
    $python = (Get-Command python.exe -ErrorAction Stop).Source
    $pythonw = Join-Path (Split-Path $python) 'pythonw.exe'
}
$python = Join-Path (Split-Path $pythonw) 'python.exe'
if (!(Test-Path $pythonw) -or !(Test-Path $script)) {
    throw 'Pythonw or Rhod600 adapter not found'
}
if ($Mode -eq 'Install') {
    if (Get-Process ShinetekTools -ErrorAction SilentlyContinue) {
        throw 'Close ShinetekTools before enabling Rhod600 direct lighting'
    }
    & $python $script --probe
    if ($LASTEXITCODE -ne 0) { throw 'Verified keyboard HID interface not found' }
    $who = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $action = New-ScheduledTaskAction -Execute $pythonw -Argument ('"' + $script + '" --serve --enable-hardware') -WorkingDirectory $PSScriptRoot
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $who
    $principal = New-ScheduledTaskPrincipal -UserId $who -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Optional verified 6-zone Rhod 600 RGB notifications; pairs with True Mouse Art ntfy bridge' -Force | Out-Null
    Start-ScheduledTask -TaskName $name
    Write-Output "Installed and requested start of $name"
}
if ($Mode -in @('Stop','Uninstall')) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($task) { Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue }
    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -in @('pythonw.exe','python.exe') -and
        $_.CommandLine -and $_.CommandLine.Contains($script)
    }
    foreach ($p in $processes) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Output "Stopped Rhod600 adapter PID $($p.ProcessId)"
    }
    if ($Mode -eq 'Uninstall' -and $task) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
        Write-Output 'Removed Rhod600 startup task'
    }
}
if ($Mode -eq 'Status' -or $Mode -eq 'Install') {
    Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue | Select-Object TaskName,State
    Get-NetUDPEndpoint -LocalPort 45894 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess
}
