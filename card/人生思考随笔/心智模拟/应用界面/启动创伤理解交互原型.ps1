$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = "C:\Users\llano\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$port = 8765
$url = "http://127.0.0.1:$port/创伤理解_交互原型.html"

Write-Host "Starting local static server in: $scriptDir"
Write-Host "Open URL: $url"

Start-Process -FilePath $python -ArgumentList @("-m", "http.server", "$port", "--bind", "127.0.0.1") -WorkingDirectory $scriptDir
Start-Sleep -Seconds 2
Start-Process $url
