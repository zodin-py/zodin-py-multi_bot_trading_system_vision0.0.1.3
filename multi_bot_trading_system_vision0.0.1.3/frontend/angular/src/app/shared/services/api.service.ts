import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  PriceResponse,
  WalletResponse,
  IndicatorsResponse,
  LoadCoinResponse,
  StatusResponse,
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

  // ---- Price ---------------------------------------------------------

  getPrice(coin: string = 'btc'): Observable<PriceResponse> {
    return this.http.get<PriceResponse>('/api/price', {
      params: { coin: coin.toLowerCase() },
    });
  }

  // ---- Wallet ---------------------------------------------------------

  getWallet(): Observable<WalletResponse> {
    return this.http.get<WalletResponse>('/api/wallet');
  }

  // ---- Indicators ---------------------------------------------------------

  getIndicators(coin: string = 'btc', tf: string = '1h'): Observable<IndicatorsResponse> {
    return this.http.get<IndicatorsResponse>('/api/indicators', {
      params: { coin: coin.toLowerCase(), tf },
    });
  }
}