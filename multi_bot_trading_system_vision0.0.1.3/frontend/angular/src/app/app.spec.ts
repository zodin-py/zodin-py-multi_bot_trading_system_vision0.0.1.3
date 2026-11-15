import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { App } from './app';
import { ApiService } from './shared/services/api.service';

describe('App', () => {
  const apiServiceMock = {
    getPrice: () => of({ symbol: 'BTC', price: 50000, timestamp: '' }),
    getIndicators: () =>
      of({ symbol: 'BTC', timeframe: '1h', rsi: [], macd: [], ema: [] }),
    getWallet: () => of({ balances: [], total_usdt: 0, timestamp: '' }),
    getTrades: () => of([]),
    getRagStatus: () =>
      of({
        success: true,
        status: 'not_built',
        system_info: {
          is_built: false,
          source_files: [],
          num_chunks: 0,
          chat_configured: false,
          embedding_model: 'local-hash-ngram-v1',
          keyword_stats: null,
          vector_stats: null,
        },
      }),
    getRagSources: () => of({ success: true, sources: [] }),
    syncRagSources: () =>
      of({ success: true, status: 'success', message: 'Knowledge index updated' }),
    sendRagChat: () =>
      of({
        success: true,
        request_id: 'test-request',
        answer: 'Keine Belege gefunden.',
        status: 'insufficient_information',
        sources: [],
        insufficient_information: true,
      }),
    getRagAnalysis: () =>
      of({
        success: true,
        analysis: {
          request_id: 'test-request',
          query: 'question',
          search_query: 'question',
          retrieval_parameters: {
            top_k: 5,
            keyword_weight: 0.5,
            vector_weight: 0.5,
            embedding_model: 'local-hash-ngram-v1',
          },
          keyword_results: [],
          vector_results: [],
          combined_results: [],
          context_documents: [],
          context_characters: 0,
          retrieval_ms: 0,
          llm_ms: 0,
          response: {
            answer: 'Keine Belege gefunden.',
            status: 'insufficient_information',
            sources: [],
            insufficient_information: true,
          },
        },
      }),
    getNews: () =>
      of({ success: true, total_new: 0, total_items: 0, items: [] }),
    getCoins: () =>
      of({ success: true, coins: ['BTCUSDT'], timeframes: { '5m': '5 Minutes' } }),
    getAnalyzerCatalog: () =>
      of({ indicators: [], patterns: [], strategies: [] }),
    getCoinCandles: () =>
      of({
        success: true,
        symbol: 'BTCUSDT',
        timeframe: '5m',
        candle_count: 0,
        candles: [],
      }),
    refreshCoinCandles: () =>
      of({
        success: true,
        symbol: 'BTCUSDT',
        timeframe: '5m',
        candles_loaded: 0,
        new_candles: 0,
        duplicates_skipped: 0,
      }),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [{ provide: ApiService, useValue: apiServiceMock }],
    })
      .compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render the dashboard', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('header h1')?.textContent).toContain(
      'Multi-Bot Trading System',
    );
    expect(compiled.querySelector('app-coin-selection')).toBeTruthy();
  });
});
