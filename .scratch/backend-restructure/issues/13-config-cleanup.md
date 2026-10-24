# 13: Config Cleanup & Validation

**What to build:** Improve `config.py` with type safety and optional per-domain config sections.

**Blocked by:** 02-di-container

**Status:** ready-for-agent

- [ ] `config.py` retains global keys (Binance API, ports, coins, timeframes)
- [ ] Add Pydantic `BaseSettings` validation for critical config values
- [ ] Optional per-domain config objects (e.g., `BotConfig`, `RiskConfig`, `IndicatorConfig`)
- [ ] Environment variable defaults preserved
- [ ] Remove any domain-specific constants from global config (move to respective domains)
- [ ] `__pycache__` and `.data/` paths preserved
- [ ] Config import path stable: `from backend.config import ...` works