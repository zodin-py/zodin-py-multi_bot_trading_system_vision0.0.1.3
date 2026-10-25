import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';

import { HeaderComponent } from './header/header.component';
import { PriceCardComponent } from './kpi/price-card.component';
import { IndicatorsComponent } from './indicators/indicators.component';

import { ApiService } from './shared/services/api.service';
import { PriceResponse, IndicatorsResponse } from './shared/models/api.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HttpClientModule,
    HeaderComponent,
    PriceCardComponent,
    IndicatorsComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly refreshInterval = 5000;
  private sub?: Subscription;

  // State synced with header
  currentCoin = 'BTC';
  currentTimeframe = '1h';

  currentPrice: number | null = null;
  priceChange = '--';
  indicators: IndicatorsResponse | null = null;

  onCoinLoaded(cmd: { symbol: string; timeframe: string }): void {
    this.currentCoin = cmd.symbol;
    this.currentTimeframe = cmd.timeframe;
    this.loadAllData();
  }

  ngOnInit(): void {
    this.loadAllData();
    this.sub = interval(this.refreshInterval).subscribe(() => this.loadAllData());
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  loadAllData(): void {
    this.api.getPrice(this.currentCoin).subscribe({
      next: (p: PriceResponse) => {
        this.currentPrice = p.price;
      },
      error: (err) => console.error('Price error:', err),
    });

    this.api.getIndicators(this.currentCoin, this.currentTimeframe).subscribe({
      next: (i: IndicatorsResponse) => (this.indicators = i),
      error: (err) => console.error('Indicators error:', err),
    });
  }
}
