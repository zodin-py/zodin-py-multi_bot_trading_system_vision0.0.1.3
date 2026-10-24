# Glossary - Fachbegriffe und Definitionen

## System-Architektur

| Begriff | Definition |
|---------|------------|
| **MCP Server** | Model Context Protocol Server — Standard-Schnittstelle für KI-Assistenten (Claude Code), um Tools und Daten bereitzustellen. Läuft als separater Prozess und kommuniziert via JSON-RPC. |
| **REST-API** | Representational State Transfer API — HTTP-basierte Schnittstelle für Web-Zugriffe, unabhängig von MCP. |
| **Data Manager** | Kern-Komponente für Datenabfrage, Caching und Verteilung. Verwaltet WebSocket-Verbindung zu Binance und historische Daten. |
| **Brain** | Signal-Aggregator — gewichtet und kombiniert Signale aller Bots zu einem finalen Trading-Signal. |
| **Executor** | Trade-Ausführungs-Engine — verwaltet offene Positionen, berechnet SL/TP, führt Orders aus. |
| **Bot** | Einzige Analyse-Einheit. Jeder Bot generiert ein Signal mit Konfidenz. Unterscheidung: **Indicator Bots** (RSI, MACD, MFI) berechnen Signale aus technischen Indikatoren; **Strategy Bots** (SR, SMC, Harmonic, Trend) erkennen Preis-Patterns und Marktstruktur. |

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

## Technische Indikatoren (Quelle: tradingview-ta → TradingView scrape)

| Indikator | Zweck | Standard-Parameter |
|-----------|-------|-------------------|
| **RSI** | Relative Strength Index — misst Überkauft/Überverkauft | Periode 14, OB 70, OS 30 |
| **MACD** | Moving Average Convergence Divergence — Trend & Momentum | Fast 12, Slow 26, Signal 9 |
| **MACD.signal** | MACD Signal Line | — |
| **Stoch.K / Stoch.D** | Stochastic Oscillator | K: 14, D: 3 |
| **CCI20** | Commodity Channel Index (20) | Periode 20 |
| **ADX / ADX+DI / ADX-DI** | Average Directional Index — Trendstärke | Periode 14 |
| **AO** | Awesome Oscillator | — |
| **Mom** | Momentum | — |
| **EMA5..EMA200** | Exponential Moving Averages | 5, 10, 20, 30, 50, 100, 200 |
| **SMA5..SMA200** | Simple Moving Averages | 5, 10, 20, 30, 50, 100, 200 |
| **BB.lower / BB.upper** | Bollinger Bands | Periode 20, StdDev 2 |
| **P.SAR** | Parabolic Stop and Reverse | — |
| **Pivots (Classic/Fib/Camarilla/Woodie/DeMark)** | Support/Resistance Levels | — |
| **Ichimoku.BLine** | Ichimoku Base Line | — |
| **VWMA** | Volume Weighted MA | — |
| **HullMA9** | Hull Moving Average | Periode 9 |
| **UO** | Ultimate Oscillator | — |
| **W.R** | Williams %R | — |
| **BBPower** | Bollinger Band Power | — |
| **close, open, high, low, volume, change** | OHLCV + Volume | — |

> **Hinweis**: Alle Indikatoren werden via `tradingview-ta` von TradingView gescraped (inoffiziell, Rate-Limits möglich). **MFI, ATR sind nicht in tradingview-ta enthalten** → lokale Berechnung als Fallback in `IndicatorProvider`.

## Strategien (Pattern/Struktur-Erkennung)

| Strategie | Zweck | Standard-Parameter |
|-----------|-------|-------------------|
| **S/R** | Support & Resistance — Preis-Level wo Kauf-/Verkaufsdruck entsteht | Lookback 50 |
| **SMC** | Smart Money Concepts — Order Blocks & Fair Value Gaps | Lookback 100 |
| **Harmonic** | Harmonische Pattern (Gartley, Bat, Butterfly) — Fibonacci-Retracements | Lookback 200 |
| **Trend** | Trend-Following via MA Alignment (EMA 9/21/50/200) + ADX/DI | EMA periods, ADX threshold |

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

## Dateien & Struktur (geplant nach Restructure)

| Pfad | Zweck |
|------|-------|
| `config.py` | Globale Konfiguration |
| `container.py` | DI Container — Service-Instanzen & Wiring |
| `launcher.py` | Entry Point — startet FastAPI + Angular Dev Server |
| `main.py` | FastAPI App Factory (`create_app`) |
| `domains/data/` | Market Data (REST, WS, Cache, Provider) |
| `domains/indicators/` | Indikator-Abruf via `tradingview-ta` (RSI, MACD, Stoch, ADX, EMAs, SMAs, BB, Pivots...) + lokaler Fallback für MFI, ATR |
| `domains/strategies/` | Strategie-Bots (SR, SMC, Harmonic, Trend) |
| `domains/analysis/` | Aggregation (Brain) + AnalysisService |
| `domains/execution/` | Order-Ausführung, SL/TP, Position-Sizing |
| `domains/trades/` | Trade-Lifecycle, History, Persistenz |
| `domains/portfolio/` | Kapital, P&L, Aggregation |
| `domains/risk/` | Daily Loss Limit, Cooldown, Trading Halt |
| `domains/api/` | FastAPI Routes, Models, Dependencies |

## Status-Codes

| Code | Bedeutung |
|------|-----------|
| `OPEN` | Position ist offen |
| `CLOSED` | Position geschlossen (TP/SL/Manual) |
| `CANCELLED` | Position storniert bevor eröffnet |

---

*Erstellt: 2026-10-18 — Basierend auf Grilling-Session und Domain-Modeling*