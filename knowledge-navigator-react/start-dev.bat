@echo off
chcp 65001 >nul
rem 一键启动：FastAPI 后端（8171） + Vite 前端开发服务器
cd /d %~dp0

set "PY=C:\ProgramData\miniconda3\python.exe"
if not exist "%PY%" set "PY=python"
set "PATH=C:\Program Files\nodejs;%PATH%"

echo [1/2] 启动后端 http://localhost:8171 ...
start "KN Backend (8171)" "%PY%" backend\run.py

timeout /t 2 /nobreak >nul

echo [2/2] 启动前端开发服务器 ...
echo.
echo 远程模式：管理界面 ⚙ → 远程模式 → http://localhost:8171 → 保存
echo 或访问：  http://localhost:5173/?backend_mode=remote
echo.
npm run dev
