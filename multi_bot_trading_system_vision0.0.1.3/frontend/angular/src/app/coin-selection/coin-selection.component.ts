import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../shared/services/api.service';
import { TradingChartComponent } from '../trading-chart/trading-chart.component';
import { AnalysisComponent } from '../analysis/analysis.component';
import {
  AnalysisSignal,
  AvailableCoin,
  CandleChartData,
  CoinSelectionResponse,
} from '../shared/models/api.models';

@Component({
  selector: 'app-coin-selection',
  standalone: true,
  imports: [CommonModule, FormsModule, TradingChartComponent, AnalysisComponent],
  templateUrl: './coin-selection.component.html',
  styleUrl: './coin-selection.component.css',
})
export class CoinSelectionComponent implements OnInit, OnDestroy {
  readonly timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];
  availableCoins: AvailableCoin[] = [];
  selectedCoin = '';
  selectedTimeframe = '5m';
  chartData: CandleChartData | null = null;
  analysisSignals: AnalysisSignal[] = [];
  loading = false;
  error: string | null = null;
  candlesLoaded = 0;
  newCandles = 0;
  private refreshTimer?: ReturnType<typeof setTimeout>;

  constructor(private readonly apiService: ApiService) {}

  ngOnInit(): void {
    this.loadAvailableCoins();
  }

  loadAvailableCoins(): void {
    this.apiService.getCoins().subscribe({
      next: (response) => {
        if (!response.success) {
          this.error = 'Die Coin-Liste konnte nicht geladen werden.';
          return;
        }

        this.availableCoins = response.coins.map((symbol) => ({
          value: symbol,
          label: symbol.replace(/USDT$/, ''),
        }));

        if (this.availableCoins.length > 0) {
          this.selectedCoin = this.availableCoins[0].value;
          this.loadCoinData(this.selectedCoin, this.selectedTimeframe);
        }
      },
      error: (err: unknown) => {
        console.error('Failed to load available coins', err);
        this.error = 'Die Coin-Liste konnte nicht geladen werden.';
      },
    });
  }

  loadCoinData(symbol: string, timeframe: string): void {
    if (!symbol) return;

    this.clearRefreshTimer();
    this.selectedCoin = symbol;
    this.selectedTimeframe = timeframe;
    this.loading = true;
    this.error = null;
    this.chartData = null;
    this.analysisSignals = [];
    this.candlesLoaded = 0;
    this.newCandles = 0;

    this.refreshCandleData();
  }

  onCoinChange(symbol: string): void {
    this.loadCoinData(symbol, this.selectedTimeframe);
  }

  onTimeframeChange(timeframe: string): void {
    this.loadCoinData(this.selectedCoin, timeframe);
  }

  refreshCandleData(): void {
    if (!this.selectedCoin) return;

    this.clearRefreshTimer();
    this.loading = true;
    this.error = null;
    this.apiService
      .refreshCoinCandles(this.selectedCoin, this.selectedTimeframe)
      .subscribe({
        next: (response: CoinSelectionResponse) => {
          if (!response.success) {
            this.error = response.error || 'Kerzendaten konnten nicht aktualisiert werden.';
            this.loading = false;
            this.scheduleLiveRefresh();
            return;
          }

          this.candlesLoaded = response.candles_loaded;
          this.newCandles = response.new_candles;
          this.fetchCandleData();
        },
        error: (err: unknown) => {
          console.error('Failed to refresh candle data', err);
          this.error = 'Kerzendaten konnten nicht aktualisiert werden.';
          this.loading = false;
          this.scheduleLiveRefresh();
        },
      });
  }

  ngOnDestroy(): void {
    this.clearRefreshTimer();
  }

  private fetchCandleData(): void {
    this.apiService
      .getCoinCandles(this.selectedCoin, this.selectedTimeframe, 1000)
      .subscribe({
        next: (response: CandleChartData) => {
          if (!response.success) {
            this.error = response.error || 'Keine Kerzendaten verfügbar.';
            this.loading = false;
            this.scheduleLiveRefresh();
            return;
          }

          this.chartData = response;
          this.candlesLoaded = response.candle_count || response.candles.length;
          this.loading = false;
          this.scheduleLiveRefresh();
        },
        error: (err: unknown) => {
          console.error(
            `Failed to load candle data for ${this.selectedCoin}/${this.selectedTimeframe}`,
            err,
          );
          this.error = `Kerzendaten für ${this.selectedCoin} konnten nicht geladen werden.`;
          this.loading = false;
          this.scheduleLiveRefresh();
        },
      });
  }

  private scheduleLiveRefresh(): void {
    this.clearRefreshTimer();
    const intervalMilliseconds: Record<string, number> = {
      '1m': 60_000,
      '5m': 300_000,
      '15m': 900_000,
      '1h': 3_600_000,
      '4h': 14_400_000,
      '1d': 86_400_000,
    };
    const interval = intervalMilliseconds[this.selectedTimeframe] ?? 300_000;
    const delay = interval - (Date.now() % interval) + 1_500;
    this.refreshTimer = setTimeout(() => this.refreshCandleData(), delay);
  }

  private clearRefreshTimer(): void {
    if (this.refreshTimer !== undefined) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = undefined;
    }
  }

  onAnalysisSignalsChange(signals: AnalysisSignal[]): void {
    this.analysisSignals = signals;
  }
}
