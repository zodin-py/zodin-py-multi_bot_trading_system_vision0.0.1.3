import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-capital-card',
  templateUrl: './capital-card.component.html',
  styleUrl: './capital-card.component.css',
})
export class CapitalCardComponent {
  @Input() capital: number | null = null;
  @Input() capitalChange: string = '--';
}