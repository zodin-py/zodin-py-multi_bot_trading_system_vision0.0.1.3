import { Component, Input } from '@angular/core';

export type SignalType = 'buy' | 'sell' | 'hold' | null;

@Component({
  selector: 'app-signal-card',
  templateUrl: './signal-card.component.html',
  styleUrl: './signal-card.component.css',
})
export class SignalCardComponent {
  @Input() signal: SignalType = null;
  @Input() confidence: number | null = null;

  get signalText(): string {
    if (!this.signal) return '--';
    return this.signal.toUpperCase();
  }

  get signalColorClass(): string {
    switch (this.signal) {
      case 'buy':
        return 'text-green-400';
      case 'sell':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  }
}