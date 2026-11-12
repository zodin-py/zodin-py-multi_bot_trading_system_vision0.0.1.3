import { ChangeDetectorRef, Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';

import { HeaderComponent } from './header/header.component';
import { PriceCardComponent } from './kpi/price-card.component';
import { NewsComponent } from './news/news.component';
import { WalletComponent } from './wallet/wallet.component';
import { TradesComponent } from './trades/trades.component';
import { CoinSelectionComponent } from './coin-selection/coin-selection.component';

import { ApiService } from './shared/services/api.service';
import {
  AnalysisResponse,
  IndicatorsResponse,
  PriceResponse,
  StrategyId,
} from './shared/models/api.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HttpClientModule,
    HeaderComponent,
    PriceCardComponent,
    NewsComponent,
    WalletComponent,
    TradesComponent,
    CoinSelectionComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly refreshInterval = 5000;
  private sub?: Subscription;

  // State synced with header
  currentCoin = 'BTC';
  currentTimeframe = '1h';

  currentPrice: number | null = null;
  priceChange = '--';
  indicators: IndicatorsResponse | null = null;
  readonly strategyOptions: { id: StrategyId; label: string }[] = [
    { id: 'sr', label: 'Support / Resistance' },
    { id: 'smc', label: 'Smart Money Concepts' },
    { id: 'harmonic', label: 'Harmonic' },
    { id: 'trend', label: 'Trend' },
  ];
  selectedStrategies: StrategyId[] = this.strategyOptions.map(({ id }) => id);
  analysis: AnalysisResponse | null = null;
  analysisError: string | null = null;
  analysisLoading = false;

  // Trades limit — user can set this in the UI
  tradesLimit = 10;

  onCoinLoaded(cmd: { symbol: string; timeframe: string }): void {
    this.currentCoin = cmd.symbol;
    this.currentTimeframe = cmd.timeframe;
    this.loadAllData();
  }

  toggleStrategy(strategy: StrategyId, selected: boolean): void {
    this.selectedStrategies = selected
      ? [...new Set([...this.selectedStrategies, strategy])]
      : this.selectedStrategies.filter((item) => item !== strategy);
  }

  onStrategyChange(strategy: StrategyId, event: Event): void {
    if (!(event.target instanceof HTMLInputElement)) return;
    this.toggleStrategy(strategy, event.target.checked);
  }

  runAnalysis(): void {
    if (this.analysisLoading) return;
    if (this.selectedStrategies.length === 0) {
      this.analysisError = 'Wähle mindestens eine Strategie aus.';
      this.analysis = null;
      return;
    }

    this.analysisLoading = true;
    this.analysisError = null;
    this.analysis = null;
    this.api
      .analyzeCoin(this.currentCoin, this.currentTimeframe, [...this.selectedStrategies])
      .subscribe({
        next: (result) => {
          this.analysis = result;
          this.analysisLoading = false;
          this.changeDetector.markForCheck();
        },
        error: (err: unknown) => {
          const apiMessage =
            typeof err === 'object' &&
            err !== null &&
            'error' in err &&
            typeof err.error === 'object' &&
            err.error !== null &&
            'error' in err.error &&
            typeof err.error.error === 'string'
              ? err.error.error
              : null;
          this.analysisError = apiMessage ?? 'Die Analyse konnte nicht abgeschlossen werden.';
          this.analysisLoading = false;
          this.changeDetector.markForCheck();
        },
      });
  }

  ngOnInit(): void {
    this.sub = interval(this.refreshInterval).subscribe(() => this.loadAllData());
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  loadAllData(): void {
    this.api.getPrice(this.currentCoin).subscribe({
      next: (p: PriceResponse) => {
        this.currentPrice = p.price;
        this.changeDetector.markForCheck();
      },
      error: (err) => console.error('Price error:', err),
    });

    this.api.getIndicators(this.currentCoin, this.currentTimeframe).subscribe({
      next: (i: IndicatorsResponse) => {
        this.indicators = i;
        this.changeDetector.markForCheck();
      },
      error: (err) => console.error('Indicators error:', err),
    });
  }
}
