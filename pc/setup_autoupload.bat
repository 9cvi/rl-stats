@echo off
REM Sets up automatic replay uploads to ballchasing.com.
REM Double-click this once. It runs the uploader every hour while your PC is on.
cd /d "%~dp0"

set "PYW="
for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"
if not defined PYW for /f "delims=" %%i in ('where pyw 2^>nul') do if not defined PYW set "PYW=%%i"
if not defined PYW (
  echo Python was not found. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  pause
  exit /b 1
)

schtasks /create /f /tn "RL Replay Uploader" /sc hourly /tr "\"%PYW%\" \"%~dp0rl_uploader.py\"" >nul
if errorlevel 1 (
  echo Could not create the scheduled task.
  pause
  exit /b 1
)

echo Running the first upload now...
"%PYW%" "%~dp0rl_uploader.py"
echo.
echo Done. Replays will upload to ballchasing every hour while your PC is on.
echo The log is in rl_uploader.log next to this file.
pause
