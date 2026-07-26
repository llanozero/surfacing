# Knowledge Navigator 一键开发启动（后端 8171 + 前端 7100）
# Usage: powershell -ExecutionPolicy Bypass -File .\start-dev.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Python: use miniconda if present, else fall back to PATH
$py = 'C:\ProgramData\miniconda3\python.exe'
if (-not (Test-Path $py)) { $py = 'python' }

# Node: add common install path
$nodeDir = 'C:\Program Files\nodejs'
if (Test-Path $nodeDir) { $env:PATH = "$nodeDir;$env:PATH" }

# Port cleanup helper
function Stop-PortProcess([int]$Port) {
    $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($l in $listeners) {
        $procId = $l.OwningProcess
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Host "  port $Port -> killed PID $procId" -ForegroundColor DarkYellow
        } catch {
            Write-Host "  port $Port -> PID $procId kill failed (ignored)" -ForegroundColor DarkYellow
        }
    }
}

Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
Write-Host '  Knowledge Navigator - Dev Startup' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''

# ── [1/4] Check Python dependencies ──

Write-Host '[1/4] Checking Python dependencies ...' -ForegroundColor Cyan
$pyOk = & $py -c 'import edge_tts' 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host '  Installing backend requirements ...' -ForegroundColor Yellow
    & $py -m pip install -r backend\requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host '  ERROR: pip install failed. Check Python / pip.' -ForegroundColor Red
        Read-Host 'Press Enter to exit'
        exit 1
    }
    Write-Host '  Done.' -ForegroundColor Green
} else {
    Write-Host '  All Python dependencies OK.' -ForegroundColor Green
}

# ── [2/4] Check Node.js dependencies ──

Write-Host ''
Write-Host '[2/4] Checking Node.js dependencies ...' -ForegroundColor Cyan
if (-not (Test-Path 'node_modules')) {
    Write-Host '  Installing frontend dependencies (npm install) ...' -ForegroundColor Yellow
    cmd /c 'npm install'
    if ($LASTEXITCODE -ne 0) {
        Write-Host '  ERROR: npm install failed. Check Node.js installation.' -ForegroundColor Red
        Read-Host 'Press Enter to exit'
        exit 1
    }
    Write-Host '  Done.' -ForegroundColor Green
} else {
    Write-Host '  node_modules exists - skipping install.' -ForegroundColor Green
}

# ── [3/4] Kill port processes ──

Write-Host ''
Write-Host '[3/4] Killing processes on ports 8171 / 7100 ...' -ForegroundColor Cyan
Stop-PortProcess 8171
Stop-PortProcess 7100

# ── [4/4] Start backend + frontend ──

Write-Host ''
Write-Host '[4/4] Launching backend -> http://localhost:8171 ...' -ForegroundColor Cyan
Start-Process -FilePath $py -ArgumentList 'backend\run.py' -WorkingDirectory $root

Start-Sleep -Seconds 2

# Health check
try {
    $health = Invoke-RestMethod -Uri 'http://localhost:8171/api/health' -TimeoutSec 5
    Write-Host ("      Backend ready: {0} cards / {1} nodes" -f $health.cards, $health.nodes) -ForegroundColor Green
} catch {
    Write-Host '      Warning: backend health check failed - see backend window for output' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Launching frontend dev server ...' -ForegroundColor Cyan
Write-Host ''
Write-Host '  Local mode : http://localhost:7100/'
Write-Host '  Remote mode: http://localhost:7100/?backend_mode=remote'
Write-Host '  (or click the gear icon in the StatusBar to switch)'
Write-Host ''

# Launch npm via cmd to avoid PowerShell redirection hangs with npm shim
cmd /c 'npm run dev'
