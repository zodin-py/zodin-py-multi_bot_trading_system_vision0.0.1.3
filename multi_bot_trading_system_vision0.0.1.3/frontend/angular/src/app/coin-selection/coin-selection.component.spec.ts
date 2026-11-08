import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { ApiService } from '../shared/services/api.service';
import { CoinSelectionComponent } from './coin-selection.component';

describe('CoinSelectionComponent', () => {
  it('fetches and stores candles when the first coin is loaded', async () => {
    const refreshCoinCandles = vi.fn(() =>
      of({
        success: true,
        symbol: 'BTCUSDT',
        timeframe: '5m',
        candles_loaded: 500,
        new_candles: 500,
        duplicates_skipped: 0,
      }),
    );
    const getCoinCandles = vi.fn(() =>
      of({
        success: true,
        symbol: 'BTCUSDT',
        timeframe: '5m',
        candle_count: 500,
        candles: [],
      }),
    );
    const apiServiceMock = {
      getCoins: () =>
        of({
          success: true,
          coins: ['BTCUSDT'],
          timeframes: { '5m': '5 Minutes' },
        }),
      refreshCoinCandles,
      getCoinCandles,
    };

    await TestBed.configureTestingModule({
      imports: [CoinSelectionComponent],
      providers: [{ provide: ApiService, useValue: apiServiceMock }],
    }).compileComponents();

    const fixture = TestBed.createComponent(CoinSelectionComponent);
    fixture.detectChanges();

    expect(refreshCoinCandles).toHaveBeenCalledWith('BTCUSDT', '5m');
    expect(getCoinCandles).toHaveBeenCalledWith('BTCUSDT', '5m');
    expect(fixture.componentInstance.chartData?.candle_count).toBe(500);
  });
});
