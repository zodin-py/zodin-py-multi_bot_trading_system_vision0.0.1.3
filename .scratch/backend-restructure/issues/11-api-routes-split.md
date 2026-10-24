# 11: API Routes Split

**What to build:** Split the monolithic `api/server.py` (319 lines) into domain-specific route files under `domains/api/routes/`.

**Blocked by:** 07-analysis-service, 09-trades-domain, 10-portfolio-risk, 02-di-container

**Status:** completed

- [ ] `domains/api/models.py` — Pydantic request/response models (AnalyzeRequest, AnalyzeResponse, IndicatorsResponse, MarketDataResponse, TradeRequest, etc.)
- [ ] `domains/api/dependencies.py` — FastAPI `Depends()` for DI container services (AnalysisService, TradeService, etc.)
- [ ] `domains/api/routes/analysis.py` — `/api/v1/analyze`, `/api/v1/indicators`, `/api/v1/market-data`, `/api/v1/symbols`, `/api/v1/timeframes`
- [ ] `domains/api/routes/trades.py` — `/api/v1/trades` (GET/POST), `/api/v1/trades/{trade_id}` (DELETE), `/api/v1/trades/history`
- [ ] `domains/api/routes/portfolio.py` — `/api/v1/portfolio`, `/api/v1/risk/limit`
- [ ] `domains/api/routes/health.py` — `/health`
- [ ] `main.py` — FastAPI app factory importing all route modules
- [ ] CORS middleware configured (allow Angular dev/prod origins)
- [ ] API tags per domain in OpenAPI/Swagger
- [ ] Old `api/server.py` deprecated
- [ ] All endpoints tested (Swagger UI accessible)