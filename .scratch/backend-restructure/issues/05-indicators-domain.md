# 05: Indicators Domain (tradingview-ta + Local Fallback)

**What to build:** Move indicator logic into `domains/indicators/` with `tradingview-ta` as primary source and local calculation fallback for MFI/ATR. Wrap behind `IndicatorProvider` protocol.

**Blocked by:** 03-domain-structure-skeleton, 02-di-container

**Status:** ready-for-agent

- [ ] `domains/indicators/models.py` — Pydantic models for indicator values (RSI, MACD, Stoch, ADX, EMAs, SMAs, BB, Pivots, etc.)
- [ ] `domains/indicators/tradingview_provider.py` — `TradingViewProvider` implementing `IndicatorProvider` protocol using `tradingview-ta`
- [ ] `domains/indicators/local_calculator.py` — Local fallback for MFI, ATR (from `indicators/calculator.py`)
- [ ] `domains/indicators/composite_provider.py` — `CompositeProvider` that tries TradingView first, falls back to local for missing indicators
- [ ] `domains/indicators/service.py` — `IndicatorService` exposing unified `get_indicators(symbol, timeframe)` interface
- [ ] `domains/indicators/__init__.py` exports public API
- [ ] Protocol `IndicatorProvider` defined (async `get_indicators(symbol, timeframe) -> IndicatorValues`)
- [ ] Old `indicators/calculator.py`, `indicators/provider.py`, `indicators/*.py` deprecated
- [ ] Config for TradingView rate limits / timeout in `config.py`