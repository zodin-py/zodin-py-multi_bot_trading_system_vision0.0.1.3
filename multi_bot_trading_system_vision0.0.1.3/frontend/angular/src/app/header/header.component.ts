import { Component, Output, EventEmitter, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

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
export class HeaderComponent implements OnInit {
  readonly timeframes = TIMEFRAMES;

  // Fixed coin list
  coins = ['BTC', 'ETH', 'SOL', 'ADA', 'BNB', 'XRP', 'LTC', 'DOT', 'DOGE', 'AVAX'];
  symbol = 'BTC';
  timeframe = '1h';

  @Output() coinLoaded = new EventEmitter<HeaderCommand>();

  private readonly api = inject(ApiService);

  ngOnInit(): void {
    this.emitLoad();
  }

  emitLoad(): void {
    this.coinLoaded.emit({ symbol: this.symbol, timeframe: this.timeframe });
  }

  onCoinChange(): void {
    this.emitLoad();
  }

  onTimeframeChange(): void {
    this.emitLoad();
  }
}
