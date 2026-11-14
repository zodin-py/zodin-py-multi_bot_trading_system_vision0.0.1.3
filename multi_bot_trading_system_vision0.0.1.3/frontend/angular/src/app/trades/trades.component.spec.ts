import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { ApiService } from '../shared/services/api.service';
import { AccountTrade } from '../shared/models/api.models';
import { TradesComponent } from './trades.component';

const accountTrade: AccountTrade = {
  id: 'BTC/USDT:123',
  symbol: 'BTC/USDT',
  side: 'buy',
  price: 100,
  amount: 1,
  cost: 100,
  timestamp: 1792953534858,
  datetime: '2026-10-25T16:38:54.858Z',
  order: 'order-123',
  fee: { cost: 0.001, currency: 'BTC' },
};

const apiServiceMock = {
  getTrades: () => of([accountTrade]),
};

describe('TradesComponent', () => {
  beforeEach(async () => {
    apiServiceMock.getTrades = () => of([accountTrade]);

    await TestBed.configureTestingModule({
      imports: [TradesComponent],
      providers: [{ provide: ApiService, useValue: apiServiceMock }],
    }).compileComponents();
  });

  it('shows Binance account fills with their actual values', () => {
    const fixture = TestBed.createComponent(TradesComponent);
    fixture.detectChanges();

    const rendered = fixture.nativeElement as HTMLElement;
    expect(rendered.textContent).toContain('BTC/USDT');
    expect(rendered.textContent).toContain('BUY');
    expect(rendered.textContent).toContain('100');
    expect(rendered.textContent).toContain('0.001 BTC');
  });

  it('reports trade history errors', () => {
    apiServiceMock.getTrades = () => throwError(() => new Error('Trade API unavailable'));

    const fixture = TestBed.createComponent(TradesComponent);
    fixture.detectChanges();

    const rendered = fixture.nativeElement as HTMLElement;
    expect(rendered.textContent).toContain('Trades konnten nicht geladen werden.');
  });
});
