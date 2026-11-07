import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';

import { ApiService } from '../shared/services/api.service';
import { NewsItem, NewsResponse } from '../shared/models/api.models';

@Component({
  selector: 'app-news',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './news.component.html',
  styleUrl: './news.component.css',
})
export class NewsComponent implements OnInit {
  newsItems: NewsItem[] = [];
  totalNew = 0;
  totalItems = 0;
  loading = true;
  refreshing = false;
  error: string | null = null;

  constructor(
    private readonly apiService: ApiService,
    private readonly changeDetector: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.refreshNews();
  }

  refreshNews(): void {
    this.refreshing = true;
    this.error = null;
    this.apiService.getNews().subscribe({
      next: (response: NewsResponse) => {
        this.newsItems = response.items;
        this.totalNew = response.total_new;
        this.totalItems = response.total_items;
        if (!response.success) {
          this.error = response.error || 'Nachrichten konnten nicht geladen werden.';
        }
        this.loading = false;
        this.refreshing = false;
        this.changeDetector.markForCheck();
      },
      error: (err: unknown) => {
        this.error = 'Nachrichten konnten nicht geladen werden.';
        this.loading = false;
        this.refreshing = false;
        console.error('News fetch error:', err);
        this.changeDetector.markForCheck();
      },
    });
  }
}