# Ticket 07: Frontend component cleanup

Status: resolved
Type: task
Created: 2026-10-25

## Problem

Several Angular components depend on backend features that are being removed (bot signals, open trades, risk management, trade history, capital/signal KPI cards). These components should be deleted.

## Acceptance Criteria

Delete the following frontend components:
- `frontend/angular/src/app/bot-signals/` (entire directory)
- `frontend/angular/src/app/open-trades/` (entire directory)
- `frontend/angular/src/app/risk-management/` (entire directory)
- `frontend/angular/src/app/trade-history/` (entire directory)
- `frontend/angular/src/app/kpi/capital-card.component.ts` (and .html, .css, spec)
- `frontend/angular/src/app/kpi/open-trades-card.component.ts` (and .html, .css, spec)
- `frontend/angular/src/app/kpi/signal-card.component.ts` (and .html, .css, spec)

Update `app.ts` and `app.html` to remove references to deleted components.
Update `api.service.ts` to remove methods for deleted endpoints.

Keep:
- `frontend/angular/src/app/header/header.component.ts` (still needed)
- `frontend/angular/src/app/indicators/indicators.component.ts` (still needed)
- `frontend/angular/src/app/kpi/price-card.component.ts` (still needed)
- `frontend/angular/src/app/shared/` (services and models — may need updates)

## Implementation Notes

- Update `app.ts` imports to remove deleted components
- Update `app.html` to remove deleted component tags
- Update `api.service.ts` to remove methods for deleted endpoints (`getSignals`, `getOpenTrades`, `closeTrade`, `getHistory`, `getPortfolio`, `getRiskLimit`, `setRiskLimit`, `startTrading`, `stopTrading`)
- Add new methods for new endpoints: `getPrice()`, `getWallet()`, `getIndicators()`
- After deletion, verify TypeScript compiles without errors
- Keep the Angular project structure intact — only remove dead components