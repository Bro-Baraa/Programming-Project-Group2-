@echo off
REM Easy Windows startup script — starts backend + frontend
REM Just double-click this file, or run "start" in Command Prompt
REM
cd /d "%~dp0"

echo ============================================
echo  Stage Monitoring Tool — Windows Startscript
echo ============================================
echo.

REM Check if Python is available
where python >nul 2>&1 (
    python start.py
    goto done
)

where py >nul 2>&1 (
    py start.py
    goto done
)

echo.
echo ERROR: Python not found. Please install Python from https://python.org
echo        or add it to your PATH.
echo.
echo This script works WITHOUT uv — it will auto-create a regular
echo Python venv if one doesn't exist. But you DO need Python first.
echo.
pause

done:
