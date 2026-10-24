<#
.SYNOPSIS
    Erstellt eine Desktop-Verknüpfung für das Multi-Bot Trading System

.DESCRIPTION
    Dieses Skript erstellt eine Verknüpfung auf dem Desktop, die beim Doppelklick
    das Trading System startet (Frontend Build + Backend).

.NOTES
    Als Administrator ausführen, falls Probleme mit Berechtigungen auftreten.
#>

$ErrorActionPreference = "Stop"

# Pfad zum Start-Skript
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$startScript = Join-Path $projectRoot "start_trading_system.ps1"

# Prüfen ob Start-Skript existiert
if (-not (Test-Path $startScript)) {
    Write-Host "[FEHLER] start_trading_system.ps1 nicht gefunden!" -ForegroundColor Red
    Write-Host "Erwarteter Pfad: $startScript" -ForegroundColor Yellow
    Read-Host "Drücken Sie Enter zum Beenden..."
    exit 1
}

# Desktop-Pfad ermitteln
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Multi-Bot Trading System.lnk"

# PowerShell COM-Objekt für Verknüpfung erstellen
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)

# Verknüpfung konfigurieren
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -NoExit -File `"$startScript`""
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Startet das Multi-Bot Trading System (Frontend + Backend)"
$shortcut.IconLocation = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe,0"

# Verknüpfung speichern
$shortcut.Save()

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "[ERFOLG] Desktop-Verknüpfung erstellt!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Pfad: $shortcutPath" -ForegroundColor White
Write-Host ""
Write-Host "Sie können jetzt auf dem Desktop auf 'Multi-Bot Trading System' doppelklicken," -ForegroundColor White
Write-Host "um das System zu starten." -ForegroundColor White
Write-Host ""
Read-Host "Drücken Sie Enter zum Beenden..."