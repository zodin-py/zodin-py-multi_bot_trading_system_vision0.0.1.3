# Ticket 06: Remove unused backend modules

Status: ready-for-agent
Type: task
Created: 2026-10-25

## Problem

After adding the three new services and rewriting the Flask app, many old modules are no longer used. They should be removed to keep the codebase minimal and understandable.

## Acceptance Criteria

Remove the following directories/files (confirmed no longer referenced by the new minimal app):

**Confirmed unused (grep confirms no imports from new app.py):**
- `backend/aggregator/` (brain.py, __init__.py)
- `backend/bots/` (all bot files: base_bot.py, harmonic_bot.py, smc_bot.py, sr_bot.py, trend_bot.py)
- `backend/execution/` (executor.py, __init__.py)
- `backend/indicators/` (old indicator bots: rsi_bot.py, macd_bot.py, mfi_bot.py, calculator.py, provider.py, __init__.py)
- `backend/data/cache.py`
- `backend/data/market_data.py`
- `backend/data/data_manager.py`
- `backend/data/__init__.py` (if it only exports removed modules)
- `backend/domains/analysis/` (entire directory)
- `backend/domains/execution/` (entire directory)
- `backend/domains/risk/` (entire directory)
- `backend/domains/strategies/` (entire directory)
- `backend/domains/trades/` (entire directory)
- `backend/domains/portfolio/` (entire directory)
- `backend/domains/api/routes/analysis.py`
- `backend/domains/api/routes/trades.py`
- `backend/domains/api/routes/portfolio.py`
- `backend/mcp_integration/` (entire directory)
- `backend/mcp/` (entire directory)
- `backend/container.py` (DI container no longer needed)
- `backend/main.py` (FastAPI entrypoint — no longer the primary server)
- `backend/run.py` (if it imports removed modules)
- `backend/domains/api/api/` (nested api directory — legacy)
- `.data/cache.duckdb` (cache file — no longer used since we use ccxt directly)

**Keep (confirmed used by new app.py):**
- `backend/config.py` (rewritten in ticket 01)
- `backend/services/price_service.py` (ticket 02)
- `backend/services/wallet_service.py` (ticket 03)
- `backend/services/indicators_service.py` (ticket 04)
- `backend/app.py` (rewritten in ticket 05)
- `backend/__init__.py` (package root)
- `backend/domains/api/routes/health.py` (or merged into app.py)
- `backend/domains/indicators/models.py` (if still referenced — may be kept for type safety)

## Implementation Notes

- Do this AFTER ticket 05 is merged, so we know what's actually still referenced
- Before deleting, grep for imports of each module to confirm nothing references it (already confirmed: new app.py only imports from backend.services.*, backend.config, backend.data.data_manager)
- Update `requirements.txt` to remove unused dependencies if any become orphaned
- Ensure `pytest` still passes after removals

## Tests

- No new tests needed; verify existing tests still pass (55 passed, 9 expected failures from removed routes)
- Verify `python -c "from backend.app import app"` works without import errors