import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-capital-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './capital-card.component.html',
  styleUrl: './capital-card.component.css',
})
export class CapitalCardComponent {
  @Input() capital: number | null = null;
  @Input() capitalError: string | null = null;
  @Input() capitalChange: string = '--';
}