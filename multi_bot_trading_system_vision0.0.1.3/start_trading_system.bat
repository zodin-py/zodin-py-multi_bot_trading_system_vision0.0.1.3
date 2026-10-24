@echo off
REM ============================================================
REM Multi-Bot Trading System - Start Script (Batch Version)
REM ============================================================
REM Dieses Skript baut das Angular Frontend und startet den Flask Backend.
REM Das Dashboard ist danach unter http://127.0.0.1:5000 erreichbar.
REM ============================================================

chcp 65001 >nul
title Multi-Bot Trading System

echo ============================================================
echo   Multi-Bot Trading System - Start Script
echo ============================================================
echo.

REM Projekt-Root ermitteln
set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "ANGULAR_DIR=%PROJECT_ROOT%frontend\angular"
set "ANGULAR_DIST_DIR=%ANGULAR_DIR%\dist\angular"

REM 1. Node.js prüfen
echo [INFO] Pruefe Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Node.js ist nicht installiert oder nicht im PATH!
    echo Bitte installieren Sie Node.js von https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js gefunden

REM 2. npm prüfen
npm --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] npm ist nicht installiert!
    pause
    exit /b 1
)
echo [OK] npm gefunden

REM 3. Python prüfen
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert oder nicht im PATH!
    pause
    exit /b 1
)
echo [OK] Python gefunden

echo.

REM 4. Angular Dependencies installieren (falls noetig)
if not exist "%ANGULAR_DIR%\node_modules" (
    echo [INFO] Installiere Angular Dependencies...
    cd /d "%ANGULAR_DIR%"
    npm install
    if errorlevel 1 (
        echo [FEHLER] npm install fehlgeschlagen!
        pause
        exit /b 1
    )
    echo [OK] Angular Dependencies installiert
    cd /d "%PROJECT_ROOT%"
) else (
    echo [OK] Angular Dependencies bereits vorhanden
)

echo.

REM 5. Angular Frontend bauen
echo [INFO] Baue Angular Frontend (Production Build)...
cd /d "%ANGULAR_DIR%"
npm run build
if errorlevel 1 (
    echo [FEHLER] Angular Build fehlgeschlagen!
    pause
    exit /b 1
)
echo [OK] Angular Build erfolgreich!
cd /d "%PROJECT_ROOT%"

echo.

REM 6. Build-Output prüfen
if not exist "%ANGULAR_DIST_DIR%" (
    echo [WARNUNG] Angular Build Output nicht gefunden!
    echo Das System faellt auf das alte Flask-Template zurueck.
) else (
    echo [OK] Angular Build Output gefunden
)

echo.

REM 7. Python Dependencies installieren
echo [INFO] Pruefe Python Dependencies...
if exist "%PROJECT_ROOT%requirements.txt" (
    pip install -r "%PROJECT_ROOT%requirements.txt" -q
    if errorlevel 1 (
        echo [WARNUNG] pip install hatte Probleme (evtl. schon installiert)
    ) else (
        echo [OK] Python Dependencies installiert/aktualisiert
    )
) else (
    echo [WARNUNG] requirements.txt nicht gefunden!
)

echo.
echo ============================================================
echo   Starte Backend Server...
echo ============================================================
echo.
echo Das Dashboard ist erreichbar unter: http://127.0.0.1:5000
echo Druecken Sie STRG+C zum Beenden
echo.

REM 8. Backend starten
cd /d "%BACKEND_DIR%"
python run.py

pause