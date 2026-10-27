@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 python launch_local.py
) else (
 py -3.12 launch_local.py
)
if errorlevel 1 pause
