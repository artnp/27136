@echo off
chcp 65001 >nul
title GitHub Uploader - artnp/27136
echo.
echo ========================================
echo   Uploading to artnp/27136 (main)
echo ========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Github\github_upload.ps1" "%~dp0." "artnp/27136"

if %ERRORLEVEL% equ 0 (
    echo.
    echo Upload complete!
) else (
    echo.
    echo Upload had errors.
)
echo.
exit /b
