@echo off
setlocal
cd /d "%~dp0"
title Garden Plan Server - Local Web Server

echo Starting Garden Plan Local Server...
echo.

python "%~dp0server.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Python is not available or encountered an error.
    echo Opening index.html directly in your default browser...
    start "" "%~dp0index.html"
    pause
)
