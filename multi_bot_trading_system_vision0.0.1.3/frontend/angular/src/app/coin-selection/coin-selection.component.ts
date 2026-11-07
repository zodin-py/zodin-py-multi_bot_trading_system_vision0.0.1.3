import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../shared/services/api.service';
import {
  AvailableCoin,
  CandleChartData,
  CoinSelectionResponse,
} from '../shared/models/api.models';

interface ChartCandle {
  x: number;
  highY: number;
  lowY: number;
  bodyY: number;
  bodyHeight: number;
  bullish: boolean;
}

@Component({
  selector: 'app-coin-selection',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './coin-selection.component.html',
  styleUrl: './coin-selection.component.css',
})
export class CoinSelectionComponent implements OnInit {
  readonly timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];
  availableCoins: AvailableCoin[] = [];
  selectedCoin = '';
  selectedTimeframe = '5m';
  chartData: CandleChartData | null = null;
  loading = false;
  error: string | null = null;
  candlesLoaded = 0;
  newCandles = 0;

  constructor(private readonly apiService: ApiService) {}

  ngOnInit(): void {
    this.loadAvailableCoins();
  }

  get chartCandles(): ChartCandle[] {
    const candles = this.chartData?.candles ?? [];
    if (candles.length === 0) return [];

    const highest = Math.max(...candles.map((candle) => candle.high));
    const lowest = Math.min(...candles.map((candle) => candle.low));
    const range = highest - lowest || Math.max(Math.abs(highest) * 0.001, 1);
    const chartHeight = 280;
    const chartTop = 10;

    const toY = (price: number): number =>
      chartTop + ((highest - price) / range) * chartHeight;

    return candles.map((candle, index) => ({
      x: 10 + ((index + 0.5) * 980) / candles.length,
      highY: toY(candle.high),
      lowY: toY(candle.low),
      bodyY: Math.min(toY(candle.open), toY(candle.close)),
      bodyHeight: Math.max(Math.abs(toY(candle.close) - toY(candle.open)), 1),
      bullish: candle.close >= candle.open,
    }));
  }

  get candleWidth(): number {
    const count = this.chartData?.candles.length ?? 0;
    return count ? Math.max(2, Math.min(12, 490 / count)) : 4;
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

    this.selectedCoin = symbol;
    this.selectedTimeframe = timeframe;
    this.loading = true;
    this.error = null;
    this.chartData = null;
    this.candlesLoaded = 0;
    this.newCandles = 0;

    this.fetchCandleData();
  }

  onCoinChange(symbol: string): void {
    this.loadCoinData(symbol, this.selectedTimeframe);
  }

  onTimeframeChange(timeframe: string): void {
    this.loadCoinData(this.selectedCoin, timeframe);
  }

  refreshCandleData(): void {
    if (!this.selectedCoin) return;

    this.loading = true;
    this.error = null;
    this.apiService
      .refreshCoinCandles(this.selectedCoin, this.selectedTimeframe)
      .subscribe({
        next: (response: CoinSelectionResponse) => {
          if (!response.success) {
            this.error = response.error || 'Kerzendaten konnten nicht aktualisiert werden.';
            this.loading = false;
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
        },
      });
  }

  private fetchCandleData(): void {
    this.apiService
      .getCoinCandles(this.selectedCoin, this.selectedTimeframe)
      .subscribe({
        next: (response: CandleChartData) => {
          if (!response.success) {
            this.error = response.error || 'Keine Kerzendaten verfügbar.';
            this.loading = false;
            return;
          }

          this.chartData = response;
          this.candlesLoaded = response.candle_count || response.candles.length;
          this.loading = false;
        },
        error: (err: unknown) => {
          console.error(
            `Failed to load candle data for ${this.selectedCoin}/${this.selectedTimeframe}`,
            err,
          );
          this.error = `Kerzendaten für ${this.selectedCoin} konnten nicht geladen werden.`;
          this.loading = false;
        },
      });
  }
}
