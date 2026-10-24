# 06: Strategies Domain (SR, SMC, Harmonic, Trend)

**What to build:** Move the 4 strategy bots into `domains/strategies/` with a common base class and service layer. These remain local pattern recognition (no TradingView).

**Blocked by:** 03-domain-structure-skeleton, 05-indicators-domain

**Status:** completed

- [ ] `domains/strategies/base.py` — `StrategyBot` abstract base (inherits from `BaseBot` or similar)
- [ ] `domains/strategies/sr_bot.py` — Support/Resistance bot (from `bots/sr_bot.py`)
- [ ] `domains/strategies/smc_bot.py` — Smart Money Concepts bot (from `bots/smc_bot.py`)
- [ ] `domains/strategies/harmonic_bot.py` — Harmonic patterns bot (from `bots/harmonic_bot.py`)
- [ ] `domains/strategies/trend_bot.py` — Trend following bot (from `bots/trend_bot.py`)
- [ ] `domains/strategies/service.py` — `StrategiesService` managing all 4 bots, exposing `analyze_all(symbol, timeframe, provider)`
- [ ] `domains/strategies/__init__.py` exports public API
- [ ] Old `bots/sr_bot.py`, `bots/smc_bot.py`, `bots/harmonic_bot.py`, `bots/trend_bot.py` deprecated
- [ ] `bots/base_bot.py` moved to `domains/strategies/base.py` or shared location
- [ ] Indicator bots (RSI, MACD, MFI) removed — now handled by Indicators Domain