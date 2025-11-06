@echo off
title Stem Splitter Web Server
color 0A

echo.
echo ========================================
echo   Stem Splitter Pro - Web Server
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Starting Flask server...
echo.
echo Server will be available at:
echo   - Local:   http://localhost:5000
echo   - Network: http://0.0.0.0:5000
echo.
echo Opening browser in 3 seconds...
timeout /t 3 /nobreak > nul

start http://localhost:5000

echo.
echo [2/2] Server running!
echo.
echo Press Ctrl+C to stop the server
echo.

python web_app.py

pause
