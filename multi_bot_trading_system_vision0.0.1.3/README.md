# Multi Bot Trading System
Trading System mit mehreren Trading-Bots und Signal-Aggregation

## Installation
```bash
python -m pip install -r requirements.txt
```

## Starten
```bash
python backend/run.py
```

Das Dashboard ist danach unter `http://127.0.0.1:5000` erreichbar. Marktdaten werden beim ersten Aufruf des Dashboards für den ausgewählten Coin geladen.

Die separate FastAPI-REST-API kann bei Bedarf in einem zweiten Terminal gestartet werden:
```bash
python -m backend.api.server
```

## Konfiguration
Bearbeite `backend/config.py` für API-Einstellungen.

## Features
- RSI, MACD, MFI Indikatoren
- Support/Resistance Erkennung
- Smart Money Concepts (Orderblocks, FVG)
- Harmonische Pattern
- Trendanalyse
- Signal-Aggregation mit Brain
- Paper Trading Modus