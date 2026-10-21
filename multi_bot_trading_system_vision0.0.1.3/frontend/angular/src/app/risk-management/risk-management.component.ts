import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs/operators';

import { ApiService } from '../shared/services/api.service';

@Component({
  selector: 'app-risk-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './risk-management.component.html',
  styleUrl: './risk-management.component.css',
})
export class RiskManagementComponent {
  @Input() isHalted = false;
  @Input() dailyPnl: number | null = null;
  @Output() riskLimitChanged = new EventEmitter<number>();

  riskLimit = 10;
  saving = false;
  statusText = '';
  statusClass = '';

  private readonly api = inject(ApiService);

  constructor() {
    this.loadRiskLimit();
  }

  loadRiskLimit(): void {
    this.api.getRiskLimit().subscribe({
      next: (res) => (this.riskLimit = res.current_limit),
      error: (err) => console.error('Error loading risk limit:', err),
    });
  }

  saveRiskLimit(): void {
    if (this.saving || this.riskLimit <= 0) {
      this.statusText = 'Ungültiger Wert';
      this.statusClass = 'text-red-400';
      return;
    }
    this.saving = true;
    this.statusText = '';
    this.api
      .setRiskLimit(this.riskLimit)
      .pipe(finalize(() => (this.saving = false)))
      .subscribe({
        next: (res) => {
          if (res.success) {
            this.statusText = 'Gespeichert ✓';
            this.statusClass = 'text-green-400';
            this.riskLimitChanged.emit(res.current_limit);
          }
        },
        error: (err) => {
          console.error('Error setting risk limit:', err);
          this.statusText = 'Fehler';
          this.statusClass = 'text-red-400';
        },
      });
  }
}