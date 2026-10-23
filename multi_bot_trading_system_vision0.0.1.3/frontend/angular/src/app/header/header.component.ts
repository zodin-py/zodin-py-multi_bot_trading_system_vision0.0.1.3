import { Component, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs/operators';

import { TIMEFRAMES } from '../shared/models/timeframes';
import { ApiService } from '../shared/services/api.service';

export interface HeaderCommand {
  symbol: string;
  timeframe: string;
}

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.css',
})
export class HeaderComponent {
  readonly timeframes = TIMEFRAMES;

  symbol = 'BTC';
  timeframe = '1h';

  loading = false;
  tradingActive = false;
  statusText = 'Stopped';
  statusDot = 'bg-gray-500';

  @Output() coinLoaded = new EventEmitter<HeaderCommand>();
  @Output() tradingToggled = new EventEmitter<boolean>();

  private readonly api = inject(ApiService);

  loadCoin(): void {
    const symbol = this.symbol.trim().toUpperCase();
    if (!symbol) {
      return;
    }
    this.loading = true;
    this.api
      .loadCoin(symbol, this.timeframe)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (res) => {
          if (res.success) {
            this.coinLoaded.emit({ symbol: res.symbol, timeframe: res.timeframe });
          }
        },
        error: (err) => console.error('Error loading coin:', err),
      });
  }

  onSymbolKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      this.loadCoin();
    }
  }

  refreshStatus(): void {
    this.api.getStatus().subscribe({
      next: (s) => {
        this.tradingActive = s.status === 'running';
        this.statusText = s.status === 'running' ? 'Running' : 'Stopped';
        this.statusDot = s.status === 'running' ? 'bg-green-500' : 'bg-gray-500';
      },
      error: (err) => console.error('Error loading status:', err),
    });
  }

  toggleTrading(): void {
    this.api.startTrading().subscribe({
      next: () => {
        this.tradingActive = true;
        this.tradingToggled.emit(true);
        this.refreshStatus();
      },
      error: (err) => console.error('Error starting trading:', err),
    });
  }

  stopTradingAction(): void {
    this.api.stopTrading().subscribe({
      next: () => {
        this.tradingActive = false;
        this.tradingToggled.emit(false);
        this.refreshStatus();
      },
      error: (err) => console.error('Error stopping trading:', err),
    });
  }
}