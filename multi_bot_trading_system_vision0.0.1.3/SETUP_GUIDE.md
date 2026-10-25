# Multi-Bot Trading System - Setup Guide

## Installation

Installiere Python 3.11 oder neuer. Öffne PowerShell im Repository-Ordner und führe aus:

```powershell
cd .\multi_bot_trading_system_vision0.0.1.3
python -m venv "$env:USERPROFILE\venvs\multi-bot"
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" -m pip install --upgrade pip
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" -m pip install -r requirements.txt
```

## Starten des Systems

Installiere zuerst Node.js. Baue danach Angular und starte den Server im Ordner `multi_bot_trading_system_vision0.0.1.3`:

```powershell
cd .\frontend\angular
npm install
npm run build
cd ..\..
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" .\backend\run.py
```

## Web Interface

Nach dem Angular-Build liefert der Server ausschließlich das Frontend aus `frontend/angular/dist/angular/browser` aus. Das Dashboard ist unter `http://127.0.0.1:5000` verfügbar. Beim Laden eines Coins ruft die Anwendung Marktdaten von Binance ab; eine Internetverbindung ist dafür erforderlich.

Zum Beenden `Ctrl+C` im Server-Terminal drücken. Für einen späteren Start zuerst wieder in den Projektordner wechseln und die Umgebung aktivieren:

```powershell
cd .\multi_bot_trading_system_vision0.0.1.3
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" .\backend\run.py
```

## Tests

Im Projektordner mit aktivierter virtueller Umgebung:

```powershell
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" -m pytest tests
```

### Verfügbare API Endpoints:

- `GET /` - Dashboard (HTML)
- `GET /api/status` - System Status
- `GET /api/settings` - Einstellungen
- `POST /api/settings` - Einstellungen ändern
- `POST /api/trading` - Trading starten/stoppen
- `GET /api/signals` - Bot Signale
- `GET /api/indicators` - Indikator Daten
- `GET /api/trades` - Offene Trades
- `DELETE /api/trades/<trade_id>` - Trade schließen
- `GET /api/history` - Trade Historie
- `GET /api/capital` - Kapital Info

## Konfiguration

### Binance API Keys
Lege die Schlüssel **nicht** in den Python-Quellcode. Erstelle im Projektordner
`multi_bot_trading_system_vision0.0.1.3` eine Datei `.env` (neben `backend/` und
`frontend/`) und trage dort deine Schlüssel ein:

```dotenv
TRADING_BINANCE_API_KEY=dein_api_key
TRADING_BINANCE_SECRET_KEY=dein_api_secret
TRADING_USE_TESTNET=true
```

Die Konfiguration lädt `.env` beim Start aus dem aktuellen Projektordner. Die
Datei `.env` ist von Git ausgeschlossen. Im Testnet funktionieren nur API
Schlüssel, die im Binance-Testnet erstellt wurden. **TESTNET bleibt standardmäßig
aktiv**; für Live-Handel darf `TRADING_USE_TESTNET` nicht leichtfertig auf
`false` gesetzt werden.

Für dein echtes Binance-Konto muss in `.env` ausdrücklich
`TRADING_USE_TESTNET=false` stehen. Dann zeigt das Dashboard das gesamte
USDT-Guthaben (frei und in offenen Orders gebunden) und die Order-Ausführung
verwendet ebenfalls Binance Live. Dafür muss der Binance-API-Schlüssel
Kontostand lesen und Spot-Trading ausführen dürfen. **Auszahlungen niemals
aktivieren.** Ein Fehler beim Abrufen wird angezeigt; das Dashboard ersetzt ihn
nicht still durch das Papier-Startkapital von 10.000.

### Trading Parameter
In `backend/config.py` können folgende Parameter angepasst werden:
- `COINS` - Handelbare Kryptowährungen
- `TIMEFRAMES` - Zeitrahmen
- `RISK_PERCENT` - Risiko pro Trade
- `MAX_OPEN_TRADES` - Max. offene Positionen
- `BOT_WEIGHTS` - Gewichte der einzelnen Bots

## System-Module

### Bots
- **RSI Bot** - Relative Strength Index
- **MACD Bot** - Moving Average Convergence Divergence
- **MFI Bot** - Money Flow Index
- **SR Bot** - Support & Resistance
- **SMC Bot** - Smart Money Concepts
- **Harmonic Bot** - Harmonic Patterns
- **Trend Bot** - Trend Analysis

### Core Komponenten
- **Brain** - Signal Aggregation & Entscheidungsfindung
- **Data Manager** - Datenmanagement & WebSocket
- **Executor** - Trade Execution & Risk Management
- **Dashboard** - Web-basierte Benutzeroberfläche

## Fehlerbehebung

### Problem: Module not found
- Stelle sicher, dass du dich im richtigen Verzeichnis befindest
- Virtual Environment muss aktiviert sein

### Problem: Flask läuft nicht
- Überprüfe Port 5000 (nicht von anderem Prozess belegt)
- Firewall-Einstellungen überprüfen

### Problem: Keine Daten von Binance
- Binance Testnet Verbindung überprüfen
- Internetverbindung prüfen

## Weitere Informationen

- Siehe `README.md` für Projektübersicht
- `requirements.txt` für alle Dependencies
- `trades/trades_history.json` für Trade Historien
