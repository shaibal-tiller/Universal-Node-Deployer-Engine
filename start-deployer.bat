@echo off
title Universal App Deployer Launcher
cd /d "%~dp0"

echo ==============================================
echo         Universal App Deployer Setup
echo ==============================================
echo.

:: Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python is not installed.
    echo [*] Automatically downloading Python 3.11...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    
    echo [*] Installing Python silently... please wait, this may take a minute.
    start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 TargetDir="%LocalAppData%\Programs\Python\Python311"
    
    echo [*] Adding Python to local session path...
    set "PATH=%LocalAppData%\Programs\Python\Python311;%LocalAppData%\Programs\Python\Python311\Scripts;%PATH%"
) else (
    echo [OK] Python is installed.
)

echo.
echo [*] Launching Universal App Deployer...
python Universal-App-Deployer.py
if %ERRORLEVEL% NEQ 0 (
    :: Fallback if environment PATH wasn't refreshed immediately
    echo [!] Standard path failed, attempting direct install location...
    "%LocalAppData%\Programs\Python\Python311\python.exe" Universal-App-Deployer.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [X] Could not launch the GUI. You may need to restart your terminal or PC.
        pause
    )
)
