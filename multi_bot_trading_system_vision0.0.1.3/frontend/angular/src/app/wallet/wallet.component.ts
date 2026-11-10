import { ChangeDetectorRef, Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';

import { ApiService } from '../shared/services/api.service';
import { WalletResponse, WalletBalance } from '../shared/models/api.models';

@Component({
  selector: 'app-wallet',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './wallet.component.html',
  styleUrl: './wallet.component.css',
})
export class WalletComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  wallet: WalletResponse | null = null;
  loading = true;
  error: string | null = null;

  ngOnInit(): void {
    this.loadWallet();
  }

  loadWallet(): void {
    this.loading = true;
    this.error = null;
    this.api.getWallet().subscribe({
      next: (w) => {
        this.wallet = w;
        this.loading = false;
        this.changeDetector.markForCheck();
      },
      error: (err: HttpErrorResponse) => {
        const apiError = err.error;
        this.error =
          apiError &&
          typeof apiError === 'object' &&
          typeof apiError.error === 'string'
            ? apiError.error
            : 'Wallet konnte nicht geladen werden.';
        this.loading = false;
        console.error('Wallet error:', err);
        this.changeDetector.markForCheck();
      },
    });
  }
}
