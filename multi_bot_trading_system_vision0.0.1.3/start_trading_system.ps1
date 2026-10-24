<#
.SYNOPSIS
    Startet das Multi-Bot Trading System (Frontend + Backend)

.DESCRIPTION
    Dieses Skript baut das Angular Frontend und startet den Flask Backend Server.
    Das Dashboard ist danach unter http://127.0.0.1:5000 erreichbar.

.NOTES
    Erstellt von: Zidan Tarawieh
    Projekt: Multi-Bot Trading System
#>

# PowerShell Fenster offen halten bei Fehlern
$ErrorActionPreference = "Stop"

# Pfade definieren
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$backendDir = Join-Path $projectRoot "backend"
$angularDir = Join-Path $projectRoot "frontend" "angular"
$angularDistDir = Join-Path $angularDir "dist" "angular"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  Multi-Bot Trading System - Start Script" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Prüfen ob Node.js installiert ist
try {
    $nodeVersion = node --version
    Write-Host "[OK] Node.js gefunden: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Node.js ist nicht installiert oder nicht im PATH!" -ForegroundColor Red
    Write-Host "Bitte installieren Sie Node.js von https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Drücken Sie Enter zum Beenden..."
    exit 1
}

# Prüfen ob npm installiert ist
try {
    $npmVersion = npm --version
    Write-Host "[OK] npm gefunden: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] npm ist nicht installiert!" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden..."
    exit 1
}

# Prüfen ob Python installiert ist
try {
    $pythonVersion = python --version
    Write-Host "[OK] Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Python ist nicht installiert oder nicht im PATH!" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden..."
    exit 1
}

Write-Host ""

# 1. Angular Dependencies installieren (falls node_modules fehlt)
if (-not (Test-Path (Join-Path $angularDir "node_modules"))) {
    Write-Host "[INFO] Installiere Angular Dependencies..." -ForegroundColor Yellow
    Set-Location $angularDir
    try {
        npm install
        Write-Host "[OK] Angular Dependencies installiert" -ForegroundColor Green
    } catch {
        Write-Host "[FEHLER] npm install fehlgeschlagen!" -ForegroundColor Red
        Read-Host "Drücken Sie Enter zum Beenden..."
        exit 1
    }
    Set-Location $projectRoot
} else {
    Write-Host "[OK] Angular Dependencies bereits vorhanden" -ForegroundColor Green
}

Write-Host ""

# 2. Angular Frontend bauen
Write-Host "[INFO] Baue Angular Frontend (Production Build)..." -ForegroundColor Yellow
Set-Location $angularDir
try {
    npm run build
    Write-Host "[OK] Angular Build erfolgreich!" -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Angular Build fehlgeschlagen!" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden..."
    exit 1
}
Set-Location $projectRoot

Write-Host ""

# 3. Prüfen ob Build-Output existiert
if (-not (Test-Path $angularDistDir)) {
    Write-Host "[WARNUNG] Angular Build Output nicht gefunden unter: $angularDistDir" -ForegroundColor Yellow
    Write-Host "Das System fällt auf das alte Flask-Template zurück." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Angular Build Output gefunden: $angularDistDir" -ForegroundColor Green
}

Write-Host ""

# 4. Python Dependencies prüfen
Write-Host "[INFO] Prüfe Python Dependencies..." -ForegroundColor Yellow
$requirementsFile = Join-Path $projectRoot "requirements.txt"
if (Test-Path $requirementsFile) {
    try {
        pip install -r $requirementsFile -q
        Write-Host "[OK] Python Dependencies installiert/aktualisiert" -ForegroundColor Green
    } catch {
        Write-Host "[WARNUNG] pip install hatte Probleme (ignoriert, evtl. schon installiert)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARNUNG] requirements.txt nicht gefunden!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  Starte Backend Server..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Das Dashboard ist erreichbar unter: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Drücken Sie STRG+C zum Beenden" -ForegroundColor Yellow
Write-Host ""

# 5. Backend starten
Set-Location $backendDir
try {
    python run.py
} catch {
    Write-Host "[FEHLER] Backend Start fehlgeschlagen: $_" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden..."
    exit 1
}