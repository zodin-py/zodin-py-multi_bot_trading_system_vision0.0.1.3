# Multi-Bot Trading System - Setup Guide

## Status: FUNKTIONSFÄHIG ✓

Das Projekt wurde vollständig konfiguriert und ist einsatzbereit.

## Installation

### 1. Python Environment
Ein virtuelles Python-Environment (venv) wurde automatisch erstellt:
```
f:/Github projekte/zodin-py-multi_bot_trading_system_vision0.0.1.3/.venv/
```

### 2. Dependencies
Alle erforderlichen Pakete wurden installiert:
- Flask 3.0.0 (Web Framework)
- Binance Connector & python-binance (Börsen-API)
- pandas & numpy (Datenverarbeitung)
- pandas-ta (Technische Indikatoren)
- websocket-client (Real-time Daten)
- Weitere: aiohttp, orjson, cachetools

## Starten des Systems

### Option 1: Über Terminal
```bash
cd f:\Github projekte\zodin-py-multi_bot_trading_system_vision0.0.1.3\multi_bot_trading_system_vision0.0.1.2
"f:/Github projekte/zodin-py-multi_bot_trading_system_vision0.0.1.3/.venv/Scripts/python.exe" app.py
```

### Option 2: Über VS Code
- Öffne app.py
- Klick auf "Run" oder drücke F5

## Web Interface

Nach dem Start ist das Dashboard verfügbar unter:
```
http://localhost:5000
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

### Binance API Keys (optional)
In `config.py` können API Keys gesetzt werden:
```python
BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY', '')
BINANCE_SECRET_KEY = os.environ.get('BINANCE_SECRET_KEY', '')
```

Standardmäßig läuft das System im **TESTNET MODE** - keine echten Transaktionen!

### Trading Parameter
In `config.py` können folgende Parameter angepasst werden:
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
