import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  PriceResponse,
  IndicatorsResponse,
  StatusResponse,
  WalletResponse,
  Trade,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private readonly http: HttpClient) {}

  getStatus(): Observable<StatusResponse> {
    return this.http.get<StatusResponse>('/api/status');
  }

  /** Returns the fixed list of supported coin symbols, e.g. ['BTC', 'ETH', ...] */
  getCoins(): Observable<string[]> {
    return this.http.get<string[]>('/api/coins');
  }

  /**
   * Fetch live price for the given coin.
   * @param coin coin symbol without USDT suffix, e.g. 'BTC'
   */
  getPrice(coin: string): Observable<PriceResponse> {
    return this.http.get<PriceResponse>('/api/price', {
      params: { coin },
    });
  }

  /**
   * Fetch technical indicators for the given coin and timeframe.
   * @param coin  coin symbol without USDT suffix, e.g. 'BTC'
   * @param tf    timeframe, e.g. '1h'
   */
  getIndicators(coin: string, tf: string = '1h'): Observable<IndicatorsResponse> {
    return this.http.get<IndicatorsResponse>('/api/indicators', {
      params: { coin, tf },
    });
  }

  /** Fetch Binance Spot wallet balances. */
  getWallet(): Observable<WalletResponse> {
    return this.http.get<WalletResponse>('/api/wallet');
  }

  /** Fetch trades history. If n is provided, only the last n entries are returned. */
  getTrades(n?: number): Observable<Trade[]> {
    let params = new HttpParams();
    if (typeof n === 'number' && n > 0) params = params.set('limit', n.toString());
    return this.http.get<Trade[]>('/api/trades', { params });
  }
}