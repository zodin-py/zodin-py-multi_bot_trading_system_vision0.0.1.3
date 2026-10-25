import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';

import { HeaderComponent } from './header/header.component';
import { PriceCardComponent } from './kpi/price-card.component';
import { IndicatorsComponent } from './indicators/indicators.component';

import { ApiService } from './shared/services/api.service';
import { PriceResponse, WalletResponse, IndicatorsResponse } from './shared/models/api.models';

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

  // Data state
  currentPrice: number | null = null;
  priceChange = '--';
  wallet: WalletResponse | null = null;
  indicators: IndicatorsResponse | null = null;

  // Header emits
  onCoinLoaded(cmd: { symbol: string; timeframe: string }): void {
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
    this.api.getPrice().subscribe({
      next: (p: PriceResponse) => {
        this.currentPrice = p.price;
      },
      error: (err) => console.error('Price error:', err),
    });

    this.api.getWallet().subscribe({
      next: (w: WalletResponse) => (this.wallet = w),
      error: (err) => console.error('Wallet error:', err),
    });

    this.api.getIndicators().subscribe({
      next: (i: IndicatorsResponse) => (this.indicators = i),
      error: (err) => console.error('Indicators error:', err),
    });
  }
}