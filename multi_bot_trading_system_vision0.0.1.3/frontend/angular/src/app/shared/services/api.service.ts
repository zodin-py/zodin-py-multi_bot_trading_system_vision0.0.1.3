import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  AggregatedSignal,
  BotProbabilities,
  HistoryResponse,
  HistoryStats,
  IndicatorsResponse,
  LoadCoinResponse,
  OpenTradesResponse,
  PortfolioResponse,
  RiskLimitResponse,
  RiskLimitSetResponse,
  SignalsResponse,
  StatusResponse,
  Trade,
  TradingActionResponse,
} from '../models/api.models';

/**
 * Thin wrapper around the Flask REST API (backend/app.py, port 5000).
 *
 * All URLs are relative ("/api/..."). In development the Angular dev server
 * proxies them to the Flask backend via proxy.conf.json; in production the
 * Flask app itself serves the built Angular assets, so the same URLs work.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private readonly http: HttpClient) {}

  // ---- Health / status -------------------------------------------------

  getStatus(): Observable<StatusResponse> {
    return this.http.get<StatusResponse>('/api/status');
  }

  // ---- Coin / timeframe selection --------------------------------------

  loadCoin(symbol: string, timeframe: string): Observable<LoadCoinResponse> {
    return this.http.post<LoadCoinResponse>('/api/load-coin', {
      symbol: symbol.toUpperCase(),
      timeframe,
    });
  }

  setSettings(symbol: string, timeframe: string): Observable<{ success: boolean }> {
    return this.http.post<{ success: boolean }>('/api/settings', {
      symbol: symbol.toUpperCase(),
      timeframe,
    });
  }

  // ---- Signals ---------------------------------------------------------

  getSignals(): Observable<SignalsResponse> {
    return this.http.get<SignalsResponse>('/api/signals');
  }

  getIndicators(): Observable<IndicatorsResponse> {
    return this.http.get<IndicatorsResponse>('/api/indicators');
  }

  // ---- Trades ----------------------------------------------------------

  getOpenTrades(): Observable<OpenTradesResponse> {
    return this.http.get<OpenTradesResponse>('/api/trades');
  }

  closeTrade(tradeId: string, reason = 'manual'): Observable<Trade> {
    return this.http.delete<Trade>(`/api/trades/${encodeURIComponent(tradeId)}`, {
      params: { reason },
    });
  }

  getHistory(
    startDate?: string,
    endDate?: string,
  ): Observable<HistoryResponse> {
    let params = new HttpParams();
    if (startDate) params = params.set('start_date', startDate);
    if (endDate) params = params.set('end_date', endDate);
    return this.http.get<HistoryResponse>('/api/history', { params });
  }

  // ---- Portfolio / risk -------------------------------------------------

  getPortfolio(): Observable<PortfolioResponse> {
    return this.http.get<PortfolioResponse>('/api/portfolio');
  }

  getRiskLimit(): Observable<RiskLimitResponse> {
    return this.http.get<RiskLimitResponse>('/api/risk/limit');
  }

  setRiskLimit(maxDailyLossEur: number): Observable<RiskLimitSetResponse> {
    return this.http.post<RiskLimitSetResponse>('/api/risk/limit', {
      max_daily_loss_eur: maxDailyLossEur,
    });
  }

  // ---- Trading control --------------------------------------------------

  startTrading(): Observable<TradingActionResponse> {
    return this.http.post<TradingActionResponse>('/api/trading', { action: 'start' });
  }

  stopTrading(): Observable<TradingActionResponse> {
    return this.http.post<TradingActionResponse>('/api/trading', { action: 'stop' });
  }
}