@echo off
set "CHROME="

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
)

if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
)

if not defined CHROME if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"
)

if not defined CHROME (
    echo Google Chrome was not found.
    echo Install Chrome or update the path inside this file.
    pause
    exit /b 1
)

set "PROFILE_DIR=%~dp0.chrome_gateway_profile"

echo Opening the authenticated gateway profile on port 9222.
start "" "%CHROME%" --remote-debugging-port=9222 --user-data-dir="%PROFILE_DIR%" "https://www.tinkercad.com/"
