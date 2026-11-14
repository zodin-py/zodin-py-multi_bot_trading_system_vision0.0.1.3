import { Component, EventEmitter, inject, Input, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {
  AnalysisResult,
  AnalysisSelection,
  AnalysisSignal,
  AnalyzerCatalog,
  AnalyzerMetadata,
  RunAnalysisResponse,
} from '../shared/models/api.models';
import { ApiService } from '../shared/services/api.service';

type AnalyzerCategory = keyof AnalyzerCatalog;
type AnalyzerConfigValue = string | number | boolean;

@Component({
  selector: 'app-analysis',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './analysis.component.html',
})
export class AnalysisComponent implements OnInit {
  private readonly api = inject(ApiService);

  @Input() symbol = 'BTCUSDT';
  @Input() timeframe = '1h';
  @Output() signalsChange = new EventEmitter<AnalysisSignal[]>();

  readonly categories: { key: AnalyzerCategory; label: string }[] = [
    { key: 'indicators', label: 'Indikatoren' },
    { key: 'patterns', label: 'Candlestick Patterns' },
    { key: 'strategies', label: 'Strategien' },
  ];

  catalog: AnalyzerCatalog = { indicators: [], patterns: [], strategies: [] };
  selected: AnalysisSelection[] = [];
  loadingCatalog = false;
  loadingAnalysis = false;
  catalogError: string | null = null;
  analysisResults: Record<string, AnalysisResult> = {};
  errors: string[] = [];
  searchTerm = '';

  ngOnInit(): void {
    this.loadCatalog();
  }

  get resultEntries(): [string, AnalysisResult][] {
    return Object.entries(this.analysisResults);
  }

  getAnalyzers(category: AnalyzerCategory): AnalyzerMetadata[] {
    const search = this.searchTerm.trim().toLocaleLowerCase();
    return this.catalog[category].filter((analyzer) =>
      `${analyzer.name} ${analyzer.description}`.toLocaleLowerCase().includes(search),
    );
  }

  isSelected(analyzerId: string): boolean {
    return this.selected.some((item) => item.analyzer_id === analyzerId);
  }

  getAnalyzerName(analyzerId: string): string {
    return (
      this.findAnalyzer(analyzerId)?.name ??
      analyzerId
    );
  }

  getConfigFields(analyzerId: string): string[] {
    return this.findAnalyzer(analyzerId)?.config_fields ?? [];
  }

  isNumericConfig(analyzerId: string, field: string): boolean {
    return typeof this.findAnalyzer(analyzerId)?.default_config?.[field] === 'number';
  }

  loadCatalog(): void {
    this.loadingCatalog = true;
    this.catalogError = null;
    this.api.getAnalyzerCatalog().subscribe({
      next: (catalog) => {
        this.catalog = catalog;
        this.loadingCatalog = false;
      },
      error: (err: unknown) => {
        console.error('Failed to load analyzer catalog', err);
        this.catalogError = 'Die verfügbaren Analyzer konnten nicht geladen werden.';
        this.loadingCatalog = false;
      },
    });
  }

  toggleAnalyzer(analyzer: AnalyzerMetadata): void {
    const existing = this.selected.find((item) => item.analyzer_id === analyzer.id);
    if (existing) {
      this.removeSelection(analyzer.id);
      return;
    }

    this.selected = [
      ...this.selected,
      { analyzer_id: analyzer.id, mode: 'current', config: {} },
    ];
    this.api.getAnalyzerMetadata(analyzer.id).subscribe({
      next: (metadata) => {
        this.catalog = {
          ...this.catalog,
          [this.categoryKey(metadata.category)]: this.catalog[
            this.categoryKey(metadata.category)
          ].map((item) => (item.id === metadata.id ? metadata : item)),
        };
        this.selected = this.selected.map((item) =>
          item.analyzer_id === metadata.id
            ? { ...item, config: metadata.default_config ?? {} }
            : item,
        );
      },
      error: (err: unknown) => {
        console.error(`Failed to load configuration for ${analyzer.id}`, err);
        this.errors = [`Konfiguration für ${analyzer.name} konnte nicht geladen werden.`];
      },
    });
  }

  updateMode(analyzerId: string, mode: 'current' | 'history'): void {
    this.selected = this.selected.map((item) =>
      item.analyzer_id === analyzerId ? { ...item, mode } : item,
    );
    delete this.analysisResults[analyzerId];
    this.emitSignals();
  }

  updateConfig(analyzerId: string, field: string, value: string | number): void {
    const configValue: AnalyzerConfigValue =
      this.isNumericConfig(analyzerId, field) && value !== '' ? Number(value) : value;
    this.selected = this.selected.map((item) =>
      item.analyzer_id === analyzerId
        ? { ...item, config: { ...item.config, [field]: configValue } }
        : item,
    );
    delete this.analysisResults[analyzerId];
    this.emitSignals();
  }

  removeSelection(analyzerId: string): void {
    this.selected = this.selected.filter((item) => item.analyzer_id !== analyzerId);
    const { [analyzerId]: _removed, ...remainingResults } = this.analysisResults;
    this.analysisResults = remainingResults;
    this.emitSignals();
  }

  removeAll(): void {
    this.selected = [];
    this.analysisResults = {};
    this.errors = [];
    this.emitSignals();
  }

  runAnalysis(): void {
    if (!this.symbol || this.selected.length === 0 || this.loadingAnalysis) return;

    this.loadingAnalysis = true;
    this.errors = [];
    this.analysisResults = {};
    this.emitSignals();

    this.api
      .runAnalysis({
        symbol: this.symbol,
        timeframe: this.timeframe,
        mode: 'current',
        selected: this.selected,
      })
      .subscribe({
        next: (response: RunAnalysisResponse) => {
          this.analysisResults = response.results ?? {};
          if (Array.isArray(response.errors)) {
            this.errors = response.errors.map(({ analyzer_id, error }) => `${analyzer_id}: ${error}`);
          } else if (typeof response.errors === 'string') {
            this.errors = [response.errors];
          } else if (response.success === false) {
            this.errors = ['Die Analyse konnte nicht ausgeführt werden.'];
          }
          this.loadingAnalysis = false;
          this.emitSignals();
        },
        error: (err: unknown) => {
          console.error('Analysis failed', err);
          this.errors = ['Die Analyse konnte nicht ausgeführt werden.'];
          this.loadingAnalysis = false;
        },
      });
  }

  private findAnalyzer(analyzerId: string): AnalyzerMetadata | undefined {
    return this.categories
      .flatMap(({ key }) => this.catalog[key])
      .find((analyzer) => analyzer.id === analyzerId);
  }

  private categoryKey(category: AnalyzerMetadata['category']): AnalyzerCategory {
    if (category === 'indicator') return 'indicators';
    if (category === 'pattern') return 'patterns';
    return 'strategies';
  }

  private emitSignals(): void {
    this.signalsChange.emit(
      Object.values(this.analysisResults).flatMap((result) => result.signals ?? []),
    );
  }
}
