# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Run the Angular frontend
```powershell
cd .\frontend\angular
npm install
npm run build
cd ..\..
```

### Run the backend API (API only mode)
```powershell
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" -m backend.api_only
```

### Run the dashboard (Flask mode)
```powershell
cd .\multi_bot_trading_system_vision0.0.1.3
& ".\\venv\\Scripts\\python.exe" backend/app.py
```

### Run tests
```powershell
& "$env:USERPROFILE\venvs\multi-bot\Scripts\python.exe" -m pytest tests
```

### Run both backend and dashboard
Start the API-only server first, then the dashboard, or use the Flask mode which serves both.

## Architecture Overview

This is a **multi-bot trading system** with the following structure:

### Backend (Python)
- `backend/app.py` - Flask dashboard server with API endpoints
- `backend/api_only.py` - FastAPI-only mode (no Angular build required)
- `backend/config.py` - Pydantic BaseSettings configuration
- `backend/services/` - Service modules:
  - `indicators_service.py` - Technical indicators (RSI, MACD, EMA) via CCXT
  - `price_service.py` - Live price feed via Binance WebSocket
  - `wallet_service.py` - Binance Spot wallet balances
- `backend/services/__init__.py` - Service initialization

### Frontend (Angular)
- `frontend/angular/src/app/` - Angular components
- Key components: `indicators/`, `wallet/`, `trades/`, `header/`, `kpi/`
- Services: `api.service.ts` for REST API calls
- Models: `api.models.ts` for type definitions

### Data Flow
1. Price service fetches live prices via Binance WebSocket (`!miniTicker@arr`)
2. Indicators service fetches OHLCV candles via CCXT and computes RSI/MACD/EMA
3. Wallet service fetches Binance Spot account balances (requires API keys)
4. Angular frontend consumes API endpoints (`/api/price`, `/api/indicators`, `/api/wallet`)

## Key Areas for Future Work

- **Indicators**: The `indicators_service.py` computes RSI, MACD, and EMA from OHLCV data. New indicator sections can be added to the Angular `indicators.component.html`.
- **News Agent**: A 4th section was recently added to the indicators component for news display - this is a UI placeholder ready for news API integration.
- **Wallet**: The `wallet_service.py` reads Binance API keys from `.env` configuration.
- **Price caching**: The `price_service.py` uses WebSocket for live prices with REST fallback.

## Important Notes

- API keys are configured via `.env` file with `TRADING_BINANCE_API_KEY` and `TRADING_BINANCE_SECRET_KEY`
- Testnet is default (`USE_TESTNET=true`); set `TRADING_USE_TESTNET=false` for live trading
- Binance API read-only permissions are required for wallet and price data
- Angular build is required for dashboard mode (`npm run build` in `frontend/angular/`)
- The backend can run in API-only mode (`python -m backend.api_only`) without Angular build