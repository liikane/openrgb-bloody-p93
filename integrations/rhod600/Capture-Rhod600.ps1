# Capture outbound 8-byte feature reports from ShinetekTools while changing ONE RGB setting.
# Passive user-mode API trace: no USB writes, keyboard hooks, or macro edits.
param([ValidateRange(5,60)][int]$Seconds = 30)
$ErrorActionPreference = 'Stop'
$process = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'ShinetekTools.exe' } | Select-Object -First 1
if (-not $process) { throw 'Open the official Rhod 600 RGB configuration app first.' }
$py = Join-Path $PSScriptRoot 'trace_vendor_feature.py'
$deps = 'C:\Users\lauri\Portable\Scripts\RGB-Uuring\analysis-deps'
if (-not (Test-Path $deps)) { throw 'Frida dependency missing. Install with python -m pip install --target <deps> frida' }
$outDir = 'C:\Users\lauri\Portable\Scripts\RGB-Uuring'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$output = Join-Path $outDir ("rhod600-outgoing-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".txt")
$old = $env:PYTHONPATH
try {
    $env:PYTHONPATH = $deps
    Write-Output 'Passive output capture now. Change ONE backlight setting in ShinetekTools.'
    Write-Output "Capture ends automatically after $Seconds seconds; no HID reports are sent."
    & python $py --pid $process.ProcessId --seconds $Seconds | Tee-Object -FilePath $output
    if ($LASTEXITCODE -ne 0) { throw 'Passive capture failed' }
    Write-Output "Local capture saved: $output"
} finally {
    $env:PYTHONPATH = $old
}
