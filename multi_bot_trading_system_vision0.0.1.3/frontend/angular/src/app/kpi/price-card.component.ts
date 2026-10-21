import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-price-card',
  templateUrl: './price-card.component.html',
  styleUrl: './price-card.component.css',
})
export class PriceCardComponent {
  @Input() price: number | null = null;
  @Input() priceChange: string = '--';
}