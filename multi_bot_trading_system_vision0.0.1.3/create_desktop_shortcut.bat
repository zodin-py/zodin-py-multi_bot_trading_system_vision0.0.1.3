@echo off
REM ============================================================
REM Erstellt Desktop-Verknüpfung für Multi-Bot Trading System
REM ============================================================

chcp 65001 >nul
title Desktop-Verknüpfung erstellen

echo ============================================================
echo   Erstelle Desktop-Verknüpfung
echo ============================================================
echo.

REM Projekt-Root ermitteln
set "PROJECT_ROOT=%~dp0"
set "START_SCRIPT=%PROJECT_ROOT%start_trading_system.bat"

REM Prüfen ob Start-Skript existiert
if not exist "%START_SCRIPT%" (
    echo [FEHLER] start_trading_system.bat nicht gefunden!
    echo Erwarteter Pfad: %START_SCRIPT%
    pause
    exit /b 1
)

REM Desktop-Pfad ermitteln
for /f "tokens=2*" %%A in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v Desktop 2^>nul') do set "DESKTOP_PATH=%%B"
if not defined DESKTOP_PATH set "DESKTOP_PATH=%USERPROFILE%\Desktop"

set "SHORTCUT_PATH=%DESKTOP_PATH%\Multi-Bot Trading System.lnk"

REM PowerShell verwenden um Verknüpfung zu erstellen (zuverlässiger als VBS)
powershell.exe -ExecutionPolicy Bypass -Command ^
    "$shell = New-Object -ComObject WScript.Shell; ^
     $shortcut = $shell.CreateShortcut('%SHORTCUT_PATH%'); ^
     $shortcut.TargetPath = 'cmd.exe'; ^
     $shortcut.Arguments = '/c \"%START_SCRIPT%\"'; ^
     $shortcut.WorkingDirectory = '%PROJECT_ROOT%'; ^
     $shortcut.Description = 'Startet das Multi-Bot Trading System (Frontend + Backend)'; ^
     $shortcut.IconLocation = '%SystemRoot%\System32\cmd.exe,0'; ^
     $shortcut.Save()"

if errorlevel 1 (
    echo [FEHLER] Konnte Verknüpfung nicht erstellen!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [ERFOLG] Desktop-Verknüpfung erstellt!
echo ============================================================
echo.
echo Pfad: %SHORTCUT_PATH%
echo.
echo Sie können jetzt auf dem Desktop auf 'Multi-Bot Trading System' doppelklicken,
echo um das System zu starten.
echo.
pause