import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AnalysisComponent } from './analysis.component';

@NgModule({
  imports: [CommonModule, FormsModule, AnalysisComponent],
  exports: [AnalysisComponent]
})
export class AnalysisModule { }