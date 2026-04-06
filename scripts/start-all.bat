@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

if /i "%1"=="stop" goto :stop
if /i "%1"=="--stop" goto :stop
goto :start

:stop
echo ================================
echo   Weibo Sentiment System - Stop
echo ================================
echo.
echo Stopping all services...
taskkill /FI "WINDOWTITLE eq Backend - Flask*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Celery Worker*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend - Vite*" /F >nul 2>&1
echo All services stopped.
pause
exit /b 0

:start
echo ================================================
echo   Weibo Sentiment System - Quick Start
echo ================================================
echo.

REM Check if Redis is running
tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I /N "redis-server.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo [CHECK] Redis is running.
) else (
    echo [WARNING] Redis is NOT running. Please start Redis server first!
)
echo.

echo [1/3] Starting Backend Server (Flask, Port 5000)...
start "Backend - Flask" cmd /k "cd /d %~dp0.. && python run.py"

echo [2/3] Starting Celery Worker...
timeout /t 2 /nobreak >nul
start "Celery Worker" cmd /k "cd /d %~dp0..\src && celery -A tasks.celery_worker worker --loglevel=info --pool=solo"

echo [3/3] Starting Frontend Server (Vite, Port 3000)...
timeout /t 2 /nobreak >nul
start "Frontend - Vite" cmd /k "cd /d %~dp0..\frontend && npm run dev"

echo.
echo ================================================
echo   Startup Complete!
echo   Backend URL:  http://127.0.0.1:5000
echo   Frontend URL: http://localhost:3000
echo ================================================
echo.
echo   Tip: Use "start-all.bat stop" to stop all services
echo.
echo Press any key to exit this window...
pause >nul
