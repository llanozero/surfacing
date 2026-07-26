@echo off
rem Knowledge Navigator - one-click dev startup (backend + frontend)
rem Pure ASCII on purpose: cmd.exe parses .bat in the system code page (GBK),
rem non-ASCII bytes would be misread and break commands.
cd /d %~dp0

set "PY=C:\ProgramData\miniconda3\python.exe"
if not exist "%PY%" set "PY=python"
set "PATH=C:\Program Files\nodejs;%PATH%"

echo.
echo ============================================
echo   Knowledge Navigator - Dev Startup
echo ============================================
echo.

echo [1/4] Checking Python dependencies ...
"%PY%" -c "import edge_tts" >nul 2>&1
if errorlevel 1 (
    echo   Installing backend requirements ...
    "%PY%" -m pip install -r backend\requirements.txt --quiet
    if errorlevel 1 (
        echo   ERROR: pip install failed. Check Python / pip.
        pause
        exit /b 1
    )
    echo   Done.
) else (
    echo   All Python dependencies OK.
)

echo.
echo [2/4] Checking Node.js dependencies ...
if not exist "node_modules\" (
    echo   Installing frontend dependencies (npm install) ...
    call npm install
    if errorlevel 1 (
        echo   ERROR: npm install failed. Check Node.js installation.
        pause
        exit /b 1
    )
    echo   Done.
) else (
    echo   node_modules exists - skipping install.
)

echo.
echo [3/4] Killing processes occupying ports 8171 / 7100 ...
for %%P in (8171 7100) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%P" ^| findstr "LISTENING"') do (
    echo   port %%P -^> kill PID %%a
    taskkill /PID %%a /F >nul 2>&1
  )
)

echo.
echo [4/4] Starting backend -^> http://localhost:8171 ...
start "KN-Backend-8171" "%PY%" backend\run.py

timeout /t 2 /nobreak >nul

echo Starting frontend dev server ...
echo.
echo   Local mode : http://localhost:7100/
echo   Remote mode: http://localhost:7100/?backend_mode=remote
echo   (or use the gear button in the StatusBar to switch)
echo.
npm run dev
