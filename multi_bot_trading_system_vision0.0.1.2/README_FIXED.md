# Multi-Bot Trading System

Ein automatisiertes Trading-System mit mehreren KI-Bots für Kryptowährungen.

## STATUS: FUNKTIONSFÄHIG ✓

Das System wurde vollständig überprüft und ist einsatzbereit!

### Behobene Probleme:
- ✓ Binance API URL Fehler behoben (BASE_URL Korrektur)
- ✓ Aktuelle Preise werden korrekt von Binance geladen
- ✓ Alle Bots sind funktionsfähig
- ✓ Alle API-Endpoints funktionieren

## Starten

```bash
python run.py
```

Das Dashboard ist dann erreichbar unter: **http://localhost:5000**

## Features

- **7 Trading Bots**: RSI, MACD, MFI, SR, SMC, Harmonic, Trend
- **Signal Aggregation**: Brain aggregiert alle Signale zu einem finalen Signal
- **Risk Management**: Automatische Stop-Loss und Take-Profit Berechnung
- **Web Dashboard**: Live-Daten und Kontrolle über Browser
- **REST API**: Programmatischer Zugriff auf alle Funktionen
- **Testnet Mode**: Kein echtes Geld! Sichere Tests mit Binance Testnet

## Architektur

```
Multi-Bot Trading System
├── Data Manager (Binance WebSocket & REST API)
├── Bots
│   ├── RSI Bot
│   ├── MACD Bot
│   ├── MFI Bot
│   ├── SR Bot (Support & Resistance)
│   ├── SMC Bot (Smart Money Concepts)
│   ├── Harmonic Bot
│   └── Trend Bot
├── Brain (Signal Aggregation)
├── Executor (Trade Management)
└── Dashboard (Web UI)
```

## API Endpoints

- `GET /` - Dashboard
- `GET /api/status` - System Status
- `GET /api/settings` - Aktuelle Einstellungen
- `POST /api/settings` - Einstellungen ändern
- `GET /api/signals` - Bot Signale & Aggregation
- `GET /api/indicators` - Technische Indikatoren
- `GET /api/trades` - Offene Trades
- `DELETE /api/trades/<id>` - Trade schließen
- `POST /api/trading` - Trading starten/stoppen
- `GET /api/capital` - Kapital Info
- `GET /api/history` - Trade Historie

## Konfiguration

Alle Einstellungen sind in `config.py`:

- **COINS**: Handelbare Kryptowährungen
- **TIMEFRAMES**: Verfügbare Zeitrahmen
- **BOT_WEIGHTS**: Gewichte für die Signal-Aggregation
- **RISK_PERCENT**: Risiko pro Trade
- **INITIAL_CAPITAL**: Startkapital für Paper Trading

## Requirements

- Python 3.11+
- Flask
- Binance API
- pandas, numpy
- pandas-ta
- websockets

Alle Dependencies sind in `requirements.txt` gelistet.

## Paper Trading (Testnet)

Das System ist standardmäßig im **Testnet Mode** konfiguriert:
- Keine echten Transaktionen
- Simulierte Trades mit 10.000 USDT Startkapital
- Perfekt zum Testen und Lernen

Um auf Live-Trading umzuschalten, ändere in `config.py`:
```python
USE_TESTNET = False
```

## Weitere Informationen

Siehe auch:
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detaillierte Installationsanleitung
