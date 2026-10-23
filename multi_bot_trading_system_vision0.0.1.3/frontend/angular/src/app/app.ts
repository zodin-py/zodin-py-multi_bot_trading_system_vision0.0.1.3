import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';

import { HeaderComponent } from './header/header.component';
import { PriceCardComponent } from './kpi/price-card.component';
import { SignalCardComponent } from './kpi/signal-card.component';
import { OpenTradesCardComponent } from './kpi/open-trades-card.component';
import { CapitalCardComponent } from './kpi/capital-card.component';
import { RiskManagementComponent } from './risk-management/risk-management.component';
import { BotSignalsComponent } from './bot-signals/bot-signals.component';
import { IndicatorsComponent } from './indicators/indicators.component';
import { OpenTradesComponent } from './open-trades/open-trades.component';
import { TradeHistoryComponent } from './trade-history/trade-history.component';

import { ApiService } from './shared/services/api.service';
import { SignalsResponse, IndicatorsResponse, OpenTradesResponse, PortfolioResponse, HistoryResponse, Trade, StatusResponse } from './shared/models/api.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HttpClientModule,
    HeaderComponent,
    PriceCardComponent,
    SignalCardComponent,
    OpenTradesCardComponent,
    CapitalCardComponent,
    RiskManagementComponent,
    BotSignalsComponent,
    IndicatorsComponent,
    OpenTradesComponent,
    TradeHistoryComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly refreshInterval = 5000;
  private sub?: Subscription;

  // Data state
  currentPrice: number | null = null;
  priceChange = '--';
  aggregatedSignal: 'buy' | 'sell' | 'hold' | null = null;
  confidence: number | null = null;
  openTradesCount = 0;
  openTradesPnl: number | null = null;
  capital: number | null = null;
  capitalChange = '--';
  dailyPnl: number | null = null;
  isHalted = false;
  riskLimit = 10;
  botProbabilities: SignalsResponse['bot_probabilities'] | null = null;
  indicators: IndicatorsResponse | null = null;
  openTrades: Trade[] = [];
  history: HistoryResponse | null = null;

  // Header emits
  onCoinLoaded(cmd: { symbol: string; timeframe: string }): void {
    this.loadAllData();
  }

  onTradingToggled(active: boolean): void {
    // status will be refreshed by the interval
  }

  ngOnInit(): void {
    // initial load
    this.loadAllData();
    // periodic refresh
    this.sub = interval(this.refreshInterval).subscribe(() => this.loadAllData());
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  loadAllData(): void {
    this.api.getStatus().subscribe({
      next: (s: StatusResponse) => {
        // status is just reflected in header
      },
      error: (err) => console.error('Status error:', err),
    });

    this.api.getSignals().subscribe({
      next: (s: SignalsResponse) => {
        this.currentPrice = s.current_price;
        this.aggregatedSignal = s.aggregated?.final_signal ?? null;
        this.confidence = s.aggregated?.confidence ?? null;
        this.botProbabilities = s.bot_probabilities ?? null;
      },
      error: (err) => console.error('Signals error:', err),
    });

    this.api.getIndicators().subscribe({
      next: (i: IndicatorsResponse) => (this.indicators = i),
      error: (err) => console.error('Indicators error:', err),
    });

    this.api.getOpenTrades().subscribe({
      next: (t: OpenTradesResponse) => {
        this.openTradesCount = t.count;
        this.openTrades = t.trades;
        // compute open trades P&L if available
        const pnl = t.trades.reduce((sum, tr) => sum + (tr.pnl ?? 0), 0);
        this.openTradesPnl = t.trades.length ? pnl : null;
      },
      error: (err) => console.error('Open trades error:', err),
    });

    this.api.getPortfolio().subscribe({
      next: (p: PortfolioResponse) => {
        this.capital = p.capital;
        this.dailyPnl = p.daily_pnl;
        this.isHalted = p.is_halted;
      },
      error: (err) => console.error('Portfolio error:', err),
    });

    this.api.getRiskLimit().subscribe({
      next: (r) => (this.riskLimit = r.current_limit),
      error: (err) => console.error('Risk limit error:', err),
    });

    this.api.getHistory().subscribe({
      next: (h: HistoryResponse) => (this.history = h),
      error: (err) => console.error('History error:', err),
    });
  }

  onHistoryLoad(event: { startDate: string; endDate: string }): void {
    this.api.getHistory(event.startDate, event.endDate).subscribe({
      next: (h: HistoryResponse) => (this.history = h),
      error: (err) => console.error('History load error:', err),
    });
  }

  onCloseTrade(tradeId: string): void {
    if (!confirm('Möchten Sie diesen Trade wirklich schließen?')) return;
    this.api.closeTrade(tradeId).subscribe({
      next: () => this.loadAllData(),
      error: (err) => console.error('Close trade error:', err),
    });
  }

  onRiskLimitChanged(limit: number): void {
    this.riskLimit = limit;
  }
}