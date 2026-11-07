import { ChangeDetectorRef, Component, inject, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ApiService } from '../shared/services/api.service';
import { Trade } from '../shared/models/api.models';

@Component({
  selector: 'app-trades',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './trades.component.html',
  styleUrl: './trades.component.css',
})
export class TradesComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  /** Wie viele der letzten Trades angezeigt werden sollen. */
  @Input() limit = 10;

  trades: Trade[] = [];
  loading = true;
  error: string | null = null;

  ngOnInit(): void {
    this.loadTrades();
  }

  loadTrades(): void {
    this.loading = true;
    this.error = null;
    this.api.getTrades(this.limit).subscribe({
      next: (t) => {
        this.trades = t;
        this.loading = false;
        this.changeDetector.markForCheck();
      },
      error: (err) => {
        this.error = 'Trades konnten nicht geladen werden.';
        this.loading = false;
        console.error('Trades error:', err);
        this.changeDetector.markForCheck();
      },
    });
  }
}
