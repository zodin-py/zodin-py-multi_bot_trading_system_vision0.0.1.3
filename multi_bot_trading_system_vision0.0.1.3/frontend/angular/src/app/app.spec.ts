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
    getNews: () =>
      of({ success: true, total_new: 0, total_items: 0, items: [] }),
    getCoins: () =>
      of({ success: true, coins: ['BTCUSDT'], timeframes: { '5m': '5 Minutes' } }),
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
