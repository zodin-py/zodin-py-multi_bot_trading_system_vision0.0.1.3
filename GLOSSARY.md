# Glossary - Fachbegriffe und Definitionen

## System-Architektur

| Begriff | Definition |
|---------|------------|
| **MCP Server** | Model Context Protocol Server — Standard-Schnittstelle für KI-Assistenten (Claude Code), um Tools und Daten bereitzustellen. Läuft als separater Prozess und kommuniziert via JSON-RPC. |
| **REST-API** | Representational State Transfer API — HTTP-basierte Schnittstelle für Web-Zugriffe, unabhängig von MCP. |
| **Data Manager** | Kern-Komponente für Datenabfrage, Caching und Verteilung. Verwaltet WebSocket-Verbindung zu Binance und historische Daten. |
| **Brain** | Signal-Aggregator — gewichtet und kombiniert Signale aller Bots zu einem finalen Trading-Signal. |
| **Executor** | Trade-Ausführungs-Engine — verwaltet offene Positionen, berechnet SL/TP, führt Orders aus. |
| **Bot** | Einzige Analyse-Einheit (RSI, MACD, MFI, SR, SMC, Harmonic, Trend). Jeder Bot generiert ein Signal mit Konfidenz. |

## Binance & API

| Begriff | Definition |
|---------|------------|
| **Testnet** | Binance Testumgebung (`testnet.binance.vision`) — simuliertes Trading ohne echtes Geld. API-Keys separat von Live. |
| **Live** | Echte Binance-Produktionsumgebung (`api.binance.com`) — echtes Geld. |
| **Kline / Candle** | Ein OHLCV-Datensatz (Open, High, Low, Close, Volume) für einen Zeitraum. |
| **OHLCV** | Open, High, Low, Close, Volume — Standardformat für Preis-Daten. |
| **Timeframe** | Zeitraum einer Kerze: 1m, 5m, 15m, 1h, 4h, 1d. |
| **Symbol** | Trading-Paar, z.B. `BTCUSDT` (Bitcoin/USDT). |

## Trading-Begriffe

| Begriff | Definition |
|---------|------------|
| **Long** | Kauf-Position — Gewinn bei steigendem Preis. |
| **Short** | Verkauf-Position — Gewinn bei fallendem Preis (Futures). |
| **Entry Price** | Preis, zu dem die Position eröffnet wird. |
| **Stop Loss (SL)** | Preis, bei dem die Position automatisch geschlossen wird um Verluste zu begrenzen. |
| **Take Profit (TP)** | Preis, bei dem die Position automatisch geschlossen wird um Gewinn zu sichern. |
| **Risk-Reward-Ratio** | Verhältnis TP/SL — hier 2:1 (TP ist doppelt so weit vom Entry wie SL). |
| **Position Size** | Anzahl Coins/Contracts in der Position — berechnet aus Risiko-Prozent. |
| **Leverage** | Hebelwirkung — multipliziert Gewinn/Verlust (nicht in Spot-Handel). |
| **Paper Trading** | Simuliertes Trading ohne echtes Geld. |
| **Drawdown** | Rückgang des Kapitals vom Hochpunkt. |
| **Max Daily Loss** | Maximal zulässiger Verlust pro Tag (hier konfigurierbar, z.B. 10€). |

## Technische Indikatoren

| Indikator | Zweck | Standard-Parameter |
|-----------|-------|-------------------|
| **RSI** | Relative Strength Index — misst Überkauft/Überverkauft | Periode 14, OB 70, OS 30 |
| **MACD** | Moving Average Convergence Divergence — Trend & Momentum | Fast 12, Slow 26, Signal 9 |
| **MFI** | Money Flow Index — RSI mit Volumen | Periode 14, OB 80, OS 20 |
| **SMA** | Simple Moving Average — Glätteter Durchschnitt | Periode variabel |
| **EMA** | Exponential Moving Average — Gewichtetere SMA | Periode variabel |
| **ADX** | Average Directional Index — Trendstärke | Periode 14, Threshold 25 |
| **S/R** | Support & Resistance — Preis-Level wo Kauf-/Verkaufsdruck entsteht | Lookback 50 |
| **SMC** | Smart Money Concepts — Order Blocks & Fair Value Gaps | Lookback 100 |
| **Harmonic** | Harmonische Pattern (Gartley, Bat, Butterfly) — Fibonacci-Retracements | Lookback 200 |

## Signal-Typen

| Signal | Bedeutung |
|--------|-----------|
| **BUY** | Long-Position eröffnen |
| **SELL** | Short-Position eröffnen |
| **HOLD** | Keine Aktion, abwarten |

## MCP Tools (geplant)

| Tool-Name | Beschreibung |
|-----------|--------------|
| `analyze_coin` | Analysiert einen Coin (Symbol + Timeframe) und gibt aggregiertes Signal zurück |
| `get_indicators` | Liefert RSI, MACD, MFI Werte für ein Symbol |
| `get_market_data` | Liefert aktuelle Preis-Daten und Kerzen |
| `open_trade` | Eröffnet einen Trade (Long/Short) mit SL/TP |
| `close_trade` | Schließt einen offenen Trade |
| `get_open_trades` | Listet alle offenen Positionen |
| `get_trade_history` | Zeigt abgeschlossene Trades |
| `set_risk_limit` | Setzt maximales Tages-Verlustlimit |
| `get_portfolio` | Zeigt aktuelles Kapital und P&L |

## Risiko-Management

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `RISK_PERCENT` | 1.0% | Risiko pro Trade als % des Kapitals |
| `RISK_REWARD_RATIO` | 2.0 | TP/SL Verhältnis |
| `MAX_OPEN_TRADES` | 5 | Maximale gleichzeitige Positionen |
| `MIN_BUY_PROBABILITY` | 65% | Minimale Buy-Konfidenz für Trade |
| `MIN_SELL_PROBABILITY` | 65% | Minimale Sell-Konfidenz für Trade |
| `MAX_DAILY_LOSS` | 10 EUR | Maximaler Verlust pro Tag |

## Dateien & Struktur

| Pfad | Zweck |
|------|-------|
| `config.py` | Alle Konfigurationsparameter |
| `data/data_manager.py` | Datenabfrage & WebSocket |
| `bots/base_bot.py` | Basisklasse aller Bots |
| `bots/*.py` | Einzelne Bot-Implementierungen |
| `indicators/*.py` | Indikator-spezifische Bots |
| `aggregator/brain.py` | Signal-Aggregation |
| `execution/executor.py` | Trade-Ausführung & SL/TP |
| `app.py` | Flask Web-Interface |
| `run.py` | Start-Skript |

## Status-Codes

| Code | Bedeutung |
|------|-----------|
| `OPEN` | Position ist offen |
| `CLOSED` | Position geschlossen (TP/SL/Manual) |
| `CANCELLED` | Position storniert bevor eröffnet |

---

*Erstellt: 2026-10-18 — Basierend auf Grilling-Session und Domain-Modeling*