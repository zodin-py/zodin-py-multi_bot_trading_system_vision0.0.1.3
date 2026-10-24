# 05: Indicators Domain (tradingview-ta + Local Fallback)

**What to build:** Move indicator logic into `domains/indicators/` with `tradingview-ta` as primary source and local calculation fallback for MFI/ATR. Wrap behind `IndicatorProvider` protocol.

**Blocked by:** 03-domain-structure-skeleton, 02-di-container

**Status:** completed

- [x] `domains/indicators/models.py` — Pydantic models (IndicatorValues with 20+ fields)
- [x] `domains/indicators/tradingview_provider.py` — `TradingViewProvider` using tradingview-ta
- [x] `domains/indicators/local_calculator.py` — Local fallback for MFI, ATR via pandas_ta
- [x] `domains/indicators/composite_provider.py` — `CompositeProvider` (TV first, local fallback)
- [x] `domains/indicators/service.py` — `IndicatorService` with unified interface
- [x] Protocol `IndicatorProvider` defined
- [x] tradingview-ta installed in project venv
