import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

import { Trade, OpenTradesResponse } from '../shared/models/api.models';

@Component({
  selector: 'app-open-trades',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './open-trades.component.html',
  styleUrl: './open-trades.component.css',
})
export class OpenTradesComponent {
  @Input() trades: Trade[] = [];
  @Output() close = new EventEmitter<string>();

  get displayTrades(): Trade[] {
    return this.trades ?? [];
  }

  getTradeId(trade: Trade): string {
    return trade.trade_id ?? trade.id ?? '';
  }

  getSideClass(side: string): string {
    return side === 'long' ? 'text-green-400' : 'text-red-400';
  }

  getSideText(side: string): string {
    return side?.toUpperCase() ?? 'LONG';
  }
}