# Multi-Bot Trading System - Setup Guide

## Installation

Installiere die in `requirements.txt` aufgeführten Abhängigkeiten in deiner Python-Umgebung:
```
python -m pip install -r requirements.txt
```

## Starten des Systems

Im Projektverzeichnis:
```bash
python backend/run.py
```

## Web Interface

Nach dem Start ist das Dashboard verfügbar unter:
```
http://127.0.0.1:5000
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
In `backend/config.py` können API Keys gesetzt werden:
```python
BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY', '')
BINANCE_SECRET_KEY = os.environ.get('BINANCE_SECRET_KEY', '')
```

Standardmäßig läuft das System im **TESTNET MODE** - keine echten Transaktionen!

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
