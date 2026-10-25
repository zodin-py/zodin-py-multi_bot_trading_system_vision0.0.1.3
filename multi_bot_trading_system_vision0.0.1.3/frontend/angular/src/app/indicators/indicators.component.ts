import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

import { IndicatorsResponse } from '../shared/models/api.models';

@Component({
  selector: 'app-indicators',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './indicators.component.html',
  styleUrl: './indicators.component.css',
})
export class IndicatorsComponent {
  @Input() indicators: IndicatorsResponse | null = null;

  // RSI helpers
  get rsiValue(): string {
    if (!this.indicators?.rsi?.length) return '--';
    return this.indicators.rsi[this.indicators.rsi.length - 1].toFixed(2);
  }

  get rsiBuy(): number {
    const v = this.indicators?.rsi?.[this.indicators.rsi.length - 1];
    if (v === undefined) return 0;
    if (v < 30) return Math.round(((30 - v) / 30) * 100);
    if (v > 70) return 0;
    return Math.round(50 - (v - 50));
  }

  get rsiSell(): number {
    const v = this.indicators?.rsi?.[this.indicators.rsi.length - 1];
    if (v === undefined) return 0;
    if (v > 70) return Math.round(((v - 70) / 30) * 100);
    if (v < 30) return 0;
    return Math.round(50 + (v - 50));
  }

  // MACD helpers
  get macdValue(): string {
    if (!this.indicators?.macd?.length) return '--';
    const m = this.indicators.macd[this.indicators.macd.length - 1];
    const s = this.indicators.macd[this.indicators.macd.length - 1]; // using macd array for signal too (per new API)
    return `MACD: ${m.toFixed(4)}, Signal: ${s.toFixed(4)}`;
  }

  get macdBuy(): number {
    if (!this.indicators?.macd?.length) return 0;
    // Use last MACD value as proxy
    return this.indicators.macd[this.indicators.macd.length - 1] > 0 ? 70 : 30;
  }

  get macdSell(): number {
    if (!this.indicators?.macd?.length) return 0;
    return this.indicators.macd[this.indicators.macd.length - 1] < 0 ? 70 : 30;
  }

  // EMA helpers
  get emaValue(): string {
    if (!this.indicators?.ema?.length) return '--';
    return this.indicators.ema[this.indicators.ema.length - 1].toFixed(2);
  }

  get emaBuy(): number {
    if (!this.indicators?.ema?.length || !this.indicators?.rsi?.length) return 0;
    // EMA trend: if price above EMA -> buy signal
    return this.indicators.rsi[this.indicators.rsi.length - 1] > this.indicators.ema[this.indicators.ema.length - 1] ? 70 : 30;
  }

  get emaSell(): number {
    if (!this.indicators?.ema?.length || !this.indicators?.rsi?.length) return 0;
    return this.indicators.rsi[this.indicators.rsi.length - 1] < this.indicators.ema[this.indicators.ema.length - 1] ? 70 : 30;
  }
}