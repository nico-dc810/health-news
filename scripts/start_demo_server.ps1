Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))
$env:PYTHONUTF8 = "1"
$pythonExe = Join-Path $env:USERPROFILE ".workbuddy\binaries\python\envs\default\Scripts\python.exe"
if (Test-Path $pythonExe) {
    & $pythonExe scripts\run_demo_server.py
} else {
    python scripts\run_demo_server.py
}
