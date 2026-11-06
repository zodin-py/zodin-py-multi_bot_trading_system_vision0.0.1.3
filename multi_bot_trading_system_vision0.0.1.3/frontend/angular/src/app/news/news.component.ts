import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

import { ApiService } from '../shared/services/api.service';
import { NewsItem } from '../shared/models/api.models';

@Component({
  selector: 'app-news',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './news.component.html',
  styleUrl: './news.component.css',
})
export class NewsComponent implements OnInit {
  newsItems: NewsItem[] = [];
  loading = true;
  error: string | null = null;

  constructor(private readonly apiService: ApiService) {}

  ngOnInit(): void {
    this.apiService.getNews().subscribe({
      next: (items) => {
        this.newsItems = items;
        this.loading = false;
      },
      error: (err: unknown) => {
        this.error = 'Failed to load news';
        this.loading = false;
        console.error('News fetch error:', err);
      },
    });
  }
}