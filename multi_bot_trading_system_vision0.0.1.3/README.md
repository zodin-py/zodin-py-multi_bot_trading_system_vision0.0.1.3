# Multi Bot Trading System
Trading System mit mehreren Trading-Bots und Signal-Aggregation

## Installation

Unter Windows PowerShell im Repository-Ordner:

```powershell
cd .\multi_bot_trading_system_vision0.0.1.3
python -m venv "$env:USERPROFILE\venvs\multi-bot"
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" -m pip install --upgrade pip
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" -m pip install -r requirements.txt
```

## Starten

Im Ordner `multi_bot_trading_system_vision0.0.1.3`:

```powershell
cd .\frontend\angular
npm install
npm run build
cd ..\..
& ".\venv\Scripts\python.exe backend/api_only.py
```

Der Server liefert das Angular-Frontend aus `frontend/angular/dist/angular/browser` aus; ein Angular-Build ist erforderlich. Das Dashboard ist danach unter `http://127.0.0.1:5000` erreichbar. Beim Laden eines Coins werden Marktdaten von Binance abgerufen; dafür ist eine Internetverbindung erforderlich.

Die separate FastAPI-REST-API kann bei Bedarf in einem zweiten Terminal gestartet werden:

```powershell
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" -m backend.api.server
```

## Tests

Im selben Ordner:

```powershell
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" -m pytest tests
```

## Konfiguration
Binance-Schlüssel werden sicher in einer `.env`-Datei im Projektordner eingetragen;
siehe [SETUP_GUIDE.md](./SETUP_GUIDE.md). Testnet ist standardmäßig aktiv. Für
Live-Kontostand und Live-Orders muss `TRADING_USE_TESTNET=false` ausdrücklich
gesetzt werden. Die API-Berechtigung für Auszahlungen darf nicht aktiviert sein.

## Crypto Information Collector

Zusätzlich zum Trading-System gibt es einen separaten, modularen Crypto Information Collector. Er wird mit `python main.py` gestartet und liest die zentrale Konfiguration aus `config.json`.

Beispiel:

```bash
cd .\multi_bot_trading_system_vision0.0.1.3
.\venv\Scripts\python.exe main.py
```

Die Datei `config.json` steuert allgemeine Quellen, überwachte Personen und einzelne Coins. Ein Eintrag kann wie folgt hinzugefügt werden:

```json
{
  "general": {
    "sources": [
      {
        "name": "Binance",
        "type": "api",
        "url": "https://api.binance.com/api/v3/ticker/24hr",
        "enabled": true,
        "items": []
      }
    ]
  },
  "people_monitoring": [
    {
      "name": "Vitalik Buterin",
      "platform": "X",
      "username": "VitalikButerin",
      "topics": ["Ethereum", "Crypto"],
      "enabled": true,
      "posts": []
    }
  ],
  "coins": [
    {
      "name": "KITE",
      "symbol": "KITE",
      "sources": [
        {
          "name": "KITE News RSS",
          "type": "rss",
          "url": "https://example.com/kite-rss.xml",
          "enabled": true,
          "items": []
        }
      ],
      "news": []
    }
  ]
}
```

Für X-Posts müssen in einer lokalen `.env`-Datei zumindest `X_BEARER_TOKEN` oder `X_API_KEY` gesetzt werden. Wenn keine Berechtigungen existieren, meldet das Programm verständlich, dass das X-Modul nicht verfügbar ist.

## Features
- RSI, MACD, MFI Indikatoren
- Support/Resistance Erkennung
- Smart Money Concepts (Orderblocks, FVG)
- Harmonische Pattern
- Trendanalyse
- Signal-Aggregation mit Brain
- Binance Testnet für Ordertests