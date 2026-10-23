import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

import { BotProbabilities } from '../shared/models/api.models';

interface BotRow {
  name: string;
  buy: number;
  sell: number;
  hold: number;
  signal: 'buy' | 'sell' | 'hold';
  timestamp: string;
}

@Component({
  selector: 'app-bot-signals',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './bot-signals.component.html',
  styleUrl: './bot-signals.component.css',
})
export class BotSignalsComponent {
  @Input() probabilities: BotProbabilities | null = null;

  get rows(): BotRow[] {
    if (!this.probabilities) return [];
    return Object.entries(this.probabilities).map(([name, data]) => ({
      name,
      buy: data.buy,
      sell: data.sell,
      hold: data.hold,
      signal: data.last_signal?.signal_type ?? 'hold',
      timestamp: data.last_signal?.timestamp
        ? new Date(data.last_signal.timestamp).toLocaleTimeString()
        : '--',
    }));
  }

  getSignalClass(signal: 'buy' | 'sell' | 'hold'): string {
    switch (signal) {
      case 'buy':
        return 'text-green-400';
      case 'sell':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  }

  getSignalText(signal: 'buy' | 'sell' | 'hold'): string {
    return signal.toUpperCase();
  }
}