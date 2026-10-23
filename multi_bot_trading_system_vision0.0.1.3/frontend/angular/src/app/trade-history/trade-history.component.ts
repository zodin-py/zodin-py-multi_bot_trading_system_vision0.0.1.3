import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { HistoryResponse, HistoryStats, Trade } from '../shared/models/api.models';

@Component({
  selector: 'app-trade-history',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './trade-history.component.html',
  styleUrl: './trade-history.component.css',
})
export class TradeHistoryComponent {
  @Input() history: HistoryResponse | null = null;
  @Output() load = new EventEmitter<{ startDate: string; endDate: string }>();

  startDate = '';
  endDate = '';

  get stats(): HistoryStats | null {
    return this.history?.stats ?? null;
  }

  get displayTrades(): Trade[] {
    return this.history?.trades?.slice(0, 20) ?? [];
  }

  loadHistory(): void {
    this.load.emit({ startDate: this.startDate, endDate: this.endDate });
  }

  getPnlClass(pnl: number | undefined): string {
    if (!pnl || pnl === 0) return 'text-gray-400';
    return pnl >= 0 ? 'text-green-400' : 'text-red-400';
  }

  getSideClass(side: string): string {
    return side === 'long' ? 'text-green-400' : 'text-red-400';
  }

  formatCloseTime(closeTime: string | undefined): string {
    if (!closeTime) return '--';
    return new Date(closeTime).toLocaleDateString();
  }
}