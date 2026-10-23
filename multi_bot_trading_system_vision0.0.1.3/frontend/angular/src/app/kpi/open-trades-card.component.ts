import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-open-trades-card',
  templateUrl: './open-trades-card.component.html',
  styleUrl: './open-trades-card.component.css',
})
export class OpenTradesCardComponent {
  @Input() count = 0;
  @Input() pnl: number | null = null;

  get pnlClass(): string {
    if (this.pnl === null) return 'text-gray-500';
    return this.pnl >= 0 ? 'text-green-400' : 'text-red-400';
  }

  get pnlText(): string {
    if (this.pnl === null) return 'P&L: --';
    const sign = this.pnl >= 0 ? '+' : '';
    return `P&L: ${sign}${this.pnl.toFixed(2)}`;
  }
}