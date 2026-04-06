@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo  Weibo Sentiment System - Frontend Only
echo ========================================
echo.

cd /d "%~dp0.."

echo [1/3] Checking Node.js environment...
node -v >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js first.
    pause
    exit /b 1
)
echo [OK] Node.js detected.

echo.
echo [2/3] Installing frontend dependencies...
call npm install --prefix frontend

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

echo.
echo [3/3] Starting frontend development server...
echo.
echo Frontend will start at http://localhost:3000
echo API requests will proxy to http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server.
echo.

call npm run dev --prefix frontend

pause
