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
    return this.indicators?.rsi?.value?.toFixed(2) ?? '--';
  }
  get rsiBuy(): number {
    const v = this.indicators?.rsi?.value;
    if (v === undefined) return 0;
    if (v < 30) return Math.round(((30 - v) / 30) * 100);
    if (v > 70) return 0;
    return Math.round(50 - (v - 50));
  }
  get rsiSell(): number {
    const v = this.indicators?.rsi?.value;
    if (v === undefined) return 0;
    if (v > 70) return Math.round(((v - 70) / 30) * 100);
    if (v < 30) return 0;
    return Math.round(50 + (v - 50));
  }

  // MACD helpers
  get macdValue(): string {
    if (!this.indicators?.macd) return '--';
    const m = this.indicators.macd;
    return `MACD: ${m.macd_line?.toFixed(4) ?? '--'}, Signal: ${m.signal_line?.toFixed(4) ?? '--'}`;
  }
  get macdBuy(): number {
    if (!this.indicators?.macd) return 0;
    return this.indicators.macd.macd_line > this.indicators.macd.signal_line ? 70 : 30;
  }
  get macdSell(): number {
    if (!this.indicators?.macd) return 0;
    return this.indicators.macd.macd_line < this.indicators.macd.signal_line ? 70 : 30;
  }

  // MFI helpers
  get mfiValue(): string {
    return this.indicators?.mfi?.value?.toFixed(2) ?? '--';
  }
  get mfiBuy(): number {
    const v = this.indicators?.mfi?.value;
    if (v === undefined) return 0;
    if (v < 20) return Math.round(((20 - v) / 20) * 100);
    if (v > 80) return 0;
    return 50;
  }
  get mfiSell(): number {
    const v = this.indicators?.mfi?.value;
    if (v === undefined) return 0;
    if (v > 80) return Math.round(((v - 80) / 20) * 100);
    if (v < 20) return 0;
    return 50;
  }
}