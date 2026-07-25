# Knowledge Navigator 一键开发启动（后端 8171 + 前端 7100）
# 用法：powershell -ExecutionPolicy Bypass -File .\start-dev.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Python：优先用户 miniconda，缺失时回退 PATH 中的 python
$py = 'C:\ProgramData\miniconda3\python.exe'
if (-not (Test-Path $py)) { $py = 'python' }

# Node：补充常见安装路径
$nodeDir = 'C:\Program Files\nodejs'
if (Test-Path $nodeDir) { $env:PATH = "$nodeDir;$env:PATH" }

# 启动前清理端口占用（8171 后端 / 7100 前端），避免重复启动失败
function Stop-PortProcess([int]$Port) {
    $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($l in $listeners) {
        $procId = $l.OwningProcess
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Host "  端口 $Port -> 已结束 PID $procId" -ForegroundColor DarkYellow
        } catch {
            Write-Host "  端口 $Port -> PID $procId 结束失败（可忽略）" -ForegroundColor DarkYellow
        }
    }
}

Write-Host '[0/2] 清理端口 8171 / 7100 占用 ...' -ForegroundColor Cyan
Stop-PortProcess 8171
Stop-PortProcess 7100

Write-Host '[1/2] 启动后端 -> http://localhost:8171 ...' -ForegroundColor Cyan
Start-Process -FilePath $py -ArgumentList 'backend\run.py' -WorkingDirectory $root

Start-Sleep -Seconds 2

# 健康检查：后端未就绪时给出明确提示
try {
    $health = Invoke-RestMethod -Uri 'http://localhost:8171/api/health' -TimeoutSec 5
    Write-Host ("      后端就绪：{0} 张卡片 / {1} 个节点" -f $health.cards, $health.nodes) -ForegroundColor Green
} catch {
    Write-Host '      警告：后端健康检查失败，请查看后端窗口输出' -ForegroundColor Yellow
}

Write-Host '[2/2] 启动前端开发服务器 ...' -ForegroundColor Cyan
Write-Host ''
Write-Host '  本地模式: http://localhost:7100/'
Write-Host '  远程模式: http://localhost:7100/?backend_mode=remote'
Write-Host '  （或在管理界面点击 ⚙ 切换远程模式）'
Write-Host ''

# 经 cmd 启动 npm：避免 PowerShell 重定向场景下 npm shim 挂起
cmd /c "npm run dev"
