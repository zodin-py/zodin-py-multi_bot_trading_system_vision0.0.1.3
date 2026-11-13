import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map, Observable } from 'rxjs';

import {
  PriceResponse,
  IndicatorsResponse,
  StatusResponse,
  WalletResponse,
  AccountTrade,
  NewsResponse,
  CoinsResponse,
  CandleChartData,
  CoinSelectionResponse,
  AnalyzerMetadata,
  AnalyzerCatalog,
  AnalysisSelection,
  AnalysisRunRequest,
  AnalysisResult,
  AnalysisSignal,
  RunAnalysisResponse,
  CandlestickPattern,
  DojiDetails,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private readonly http: HttpClient) {}

  getStatus(): Observable<StatusResponse> {
    return this.http.get<StatusResponse>('/api/status');
  }

  /** Returns the fixed list of supported coin symbols, e.g. ['BTC', 'ETH', ...] */
  getCoins(): Observable<CoinsResponse> {
    return this.http.get<CoinsResponse>('/api/coins');
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
  getTrades(n?: number): Observable<AccountTrade[]> {
    let params = new HttpParams();
    if (typeof n === 'number' && n > 0) params = params.set('limit', n.toString());
    return this.http.get<AccountTrade[]>('/api/trades', { params });
  }

  /** Collect and fetch latest news from configured sources. */
  getNews(): Observable<NewsResponse> {
    return this.http.get<NewsResponse>('/api/news');
  }

  /** Get stored candle chart data for a specific coin and timeframe. */
  getCoinCandles(
    symbol: string,
    timeframe: string = '5m',
    limit: number = 1000,
  ): Observable<CandleChartData> {
    return this.http.get<CandleChartData>(`/api/coins/${symbol}/candles`, {
      params: { timeframe, limit: limit.toString() },
    });
  }

  /** Refresh candle data for a specific coin and timeframe. */
  refreshCoinCandles(symbol: string, timeframe: string = '5m'): Observable<CoinSelectionResponse> {
    return this.http.post<CoinSelectionResponse>(`/api/coins/${symbol}/select`, { timeframe });
  }

  /** Get catalog of available analysis analyzers. */
  getAnalyzerCatalog(): Observable<AnalyzerCatalog> {
    return this.http
      .get<{ success: boolean; catalog: AnalyzerCatalog }>('/api/analysis/catalog')
      .pipe(map((response) => response.catalog));
  }

  /** Get metadata for a specific analyzer. */
  getAnalyzerMetadata(analyzerId: string): Observable<AnalyzerMetadata> {
    return this.http
      .get<{ success: boolean; metadata: AnalyzerMetadata }>(
        `/api/analysis/metadata/${encodeURIComponent(analyzerId)}`,
      )
      .pipe(map((response) => response.metadata));
  }

  /** Run selected analyzers on candle data. */
  runAnalysis(request: AnalysisRunRequest): Observable<RunAnalysisResponse> {
    return this.http.post<RunAnalysisResponse>('/api/analysis/run', request);
  }
}