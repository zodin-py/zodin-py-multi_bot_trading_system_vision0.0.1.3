# Ticket 05: Minimal Flask app serving Angular

Status: ready-for-agent
Type: task
Created: 2026-10-25

## Problem

The current `backend/app.py` is a 300+ line Flask app with trading loop, bot aggregation, execution, and many routes that are being removed. It needs to be replaced with a minimal app that only serves the Angular frontend and exposes the three new API routes.

## Acceptance Criteria

- Rewrite `backend/app.py` to be a minimal Flask app (~80 lines)
- Routes: `/api/price`, `/api/wallet`, `/api/indicators`, `/health`
- Serve Angular static files from `frontend/angular/dist/angular/browser/`
- CORS configured for `localhost:4200` and `localhost:5000`
- No trading loop, no bot initialization, no executor
- Old routes (`/api/signals`, `/api/trades`, `/api/portfolio`, `/api/risk/limit`, etc.) are removed
- The new routes are wired into the Flask app (not FastAPI — the dashboard runs on Flask port 5000)

## Implementation Notes

- The Flask app (`app.py`) runs on port 5000 and serves the Angular build
- The FastAPI server (`backend/api/server.py` / `backend/main.py`) runs on port 8000
- Per spec: "New API routes /api/price, /api/wallet, /api/indicators werden eingeführt und per Mapping-Schicht an bestehende Routen gekoppelt"
- The mapping layer means the new routes should be on the Flask app (port 5000) since that's what the Angular frontend calls
- Import services from `backend.services.price_service`, `wallet_service`, `indicators_service`
- Keep the SPA fallback route for Angular routing

## Tests

- `test_flask_app_health`: verifies `/health` returns 200
- `test_flask_app_serves_index`: verifies root path serves Angular index.html (or 503 if not built)
- `test_old_routes_removed`: verifies `/api/signals` returns 404
