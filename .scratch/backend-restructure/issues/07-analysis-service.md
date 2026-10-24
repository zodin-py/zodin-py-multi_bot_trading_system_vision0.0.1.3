# 07: Analysis Service Refactor

**What to build:** Refactor `services/analysis_service.py` into `domains/analysis/` with Brain aggregation and AnalysisService using the new Indicators + Strategies domains.

**Blocked by:** 05-indicators-domain, 06-strategies-domain, 02-di-container

**Status:** ready-for-agent

- [ ] `domains/analysis/models.py` — `AggregatedSignal`, `BotSignal`, `SignalType` Pydantic models
- [ ] `domains/analysis/brain.py` — `Brain` class (from `aggregator/brain.py`) weighting 7 bot signals
- [ ] `domains/analysis/service.py` — `AnalysisService` orchestrating: get indicators → run strategies → aggregate via Brain
- [ ] `domains/analysis/__init__.py` exports public API
- [ ] Weights from config (`BOT_WEIGHTS`) injected, not hardcoded
- [ ] Thresholds from config (`SIGNAL_THRESHOLDS`) injected
- [ ] Old `services/analysis_service.py`, `aggregator/brain.py` deprecated
- [ ] Single `analyze_coin(symbol, timeframe)` method returning full breakdown