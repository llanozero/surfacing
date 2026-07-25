@echo off
rem Knowledge Navigator - one-click dev startup (backend + frontend)
rem Pure ASCII on purpose: cmd.exe parses .bat in the system code page (GBK),
rem non-ASCII bytes would be misread and break commands.
cd /d %~dp0

set "PY=C:\ProgramData\miniconda3\python.exe"
if not exist "%PY%" set "PY=python"
set "PATH=C:\Program Files\nodejs;%PATH%"

echo [0/2] Killing processes occupying ports 8171 / 7100 ...
for %%P in (8171 7100) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%P" ^| findstr "LISTENING"') do (
    echo   port %%P -^> kill PID %%a
    taskkill /PID %%a /F >nul 2>&1
  )
)

echo [1/2] Starting backend  -^> http://localhost:8171 ...
start "KN-Backend-8171" "%PY%" backend\run.py

timeout /t 2 /nobreak >nul

echo [2/2] Starting frontend dev server ...
echo.
echo   Local mode : http://localhost:7100/
echo   Remote mode: http://localhost:7100/?backend_mode=remote
echo   (or use the gear button in the Tree view to switch)
echo.
npm run dev
