import {
  Component,
  EventEmitter,
  inject,
  Input,
  OnDestroy,
  OnInit,
  Output,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import {
  AnalysisResult,
  AnalysisSelection,
  AnalysisSignal,
  AnalyzerCatalog,
  AnalyzerMetadata,
  RunAnalysisResponse,
} from '../shared/models/api.models';
import { ApiService } from '../shared/services/api.service';
import { AnalysisSelectionService } from '../shared/services/analysis-selection.service';

type AnalyzerCategory = keyof AnalyzerCatalog;
type AnalyzerConfigValue = string | number | boolean;

@Component({
  selector: 'app-analysis',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './analysis.component.html',
})
export class AnalysisComponent implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly selectionStore = inject(AnalysisSelectionService);

  @Input() symbol = 'BTCUSDT';
  @Input() timeframe = '1h';
  @Output() signalsChange = new EventEmitter<AnalysisSignal[]>();

  readonly categories: { key: AnalyzerCategory; label: string }[] = [
    { key: 'indicators', label: 'Indikatoren' },
    { key: 'patterns', label: 'Candlestick Patterns' },
    { key: 'strategies', label: 'Strategien' },
  ];

  catalog: AnalyzerCatalog = { indicators: [], patterns: [], strategies: [] };
  loadingCatalog = false;
  loadingAnalysis = false;
  catalogError: string | null = null;
  analysisResults: Record<string, AnalysisResult> = {};
  errors: string[] = [];
  searchTerm = '';
  private analysisRequest?: Subscription;
  private readonly metadataRequests = new Map<string, Subscription>();

  get selected(): AnalysisSelection[] {
    return this.selectionStore.selections;
  }

  ngOnInit(): void {
    this.loadCatalog();
  }

  get resultEntries(): [string, AnalysisResult][] {
    return Object.entries(this.analysisResults).filter(([analyzerId]) =>
      this.isSelected(analyzerId),
    );
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
        const validSelections = this.selected.filter(
          (selection) => this.findAnalyzer(selection.analyzer_id) !== undefined,
        );
        if (validSelections.length !== this.selected.length) {
          this.setSelected(validSelections);
        }
        for (const selection of this.selected) {
          const analyzer = this.findAnalyzer(selection.analyzer_id);
          if (analyzer) this.loadAnalyzerMetadata(analyzer, false);
        }
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
    if (this.isSelected(analyzer.id)) {
      this.removeSelection(analyzer.id);
      return;
    }

    this.setSelected([
      ...this.selected,
      {
        analyzer_id: analyzer.id,
        mode: 'current',
        config: { ...(analyzer.default_config ?? {}) },
      },
    ]);
    this.loadAnalyzerMetadata(analyzer, true);
  }

  private loadAnalyzerMetadata(analyzer: AnalyzerMetadata, initializeConfig: boolean): void {
    const request = this.api.getAnalyzerMetadata(analyzer.id).subscribe({
      next: (metadata) => {
        this.metadataRequests.delete(analyzer.id);
        this.catalog = {
          ...this.catalog,
          [this.categoryKey(metadata.category)]: this.catalog[
            this.categoryKey(metadata.category)
          ].map((item) => (item.id === metadata.id ? metadata : item)),
        };
        const selected = this.selected.map((item) =>
          item.analyzer_id === metadata.id
            ? {
                ...item,
                config: initializeConfig && Object.keys(item.config).length === 0
                  ? { ...(metadata.default_config ?? {}) }
                  : item.config,
              }
            : item,
        );
        this.setSelected(selected, false);
      },
      error: (err: unknown) => {
        this.metadataRequests.delete(analyzer.id);
        console.error(`Failed to load configuration for ${analyzer.id}`, err);
        this.errors = [`Konfiguration für ${analyzer.name} konnte nicht geladen werden.`];
      },
    });
    this.metadataRequests.set(analyzer.id, request);
  }

  updateMode(analyzerId: string, mode: 'current' | 'history'): void {
    this.setSelected(this.selected.map((item) =>
      item.analyzer_id === analyzerId ? { ...item, mode } : item,
    ));
    delete this.analysisResults[analyzerId];
    this.emitSignals();
  }

  updateConfig(analyzerId: string, field: string, value: string | number): void {
    const configValue: AnalyzerConfigValue =
      this.isNumericConfig(analyzerId, field) && value !== '' ? Number(value) : value;
    this.setSelected(this.selected.map((item) =>
      item.analyzer_id === analyzerId
        ? { ...item, config: { ...item.config, [field]: configValue } }
        : item,
    ));
    delete this.analysisResults[analyzerId];
    this.emitSignals();
  }

  removeSelection(analyzerId: string): void {
    this.metadataRequests.get(analyzerId)?.unsubscribe();
    this.metadataRequests.delete(analyzerId);
    this.setSelected(this.selected.filter((item) => item.analyzer_id !== analyzerId));
    const { [analyzerId]: _removed, ...remainingResults } = this.analysisResults;
    this.analysisResults = remainingResults;
    this.emitSignals();
  }

  removeAll(): void {
    for (const request of this.metadataRequests.values()) request.unsubscribe();
    this.metadataRequests.clear();
    this.setSelected([]);
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

    this.analysisRequest = this.api
      .runAnalysis({
        symbol: this.symbol,
        timeframe: this.timeframe,
        mode: 'current',
        selected: this.selected,
      })
      .subscribe({
        next: (response: RunAnalysisResponse) => {
          const enabledIds = new Set(this.selected.map(({ analyzer_id }) => analyzer_id));
          this.analysisResults = Object.fromEntries(
            Object.entries(response.results ?? {}).filter(([analyzerId]) =>
              enabledIds.has(analyzerId),
            ),
          );
          if (Array.isArray(response.errors)) {
            this.errors = response.errors.map(({ analyzer_id, error }) => `${analyzer_id}: ${error}`);
          } else if (typeof response.errors === 'string') {
            this.errors = [response.errors];
          } else if (response.success === false) {
            this.errors = ['Die Analyse konnte nicht ausgeführt werden.'];
          }
          this.loadingAnalysis = false;
          this.analysisRequest = undefined;
          this.emitSignals();
        },
        error: (err: unknown) => {
          console.error('Analysis failed', err);
          this.errors = ['Die Analyse konnte nicht ausgeführt werden.'];
          this.loadingAnalysis = false;
          this.analysisRequest = undefined;
        },
      });
  }

  ngOnDestroy(): void {
    this.analysisRequest?.unsubscribe();
    for (const request of this.metadataRequests.values()) request.unsubscribe();
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
      Object.entries(this.analysisResults)
        .filter(([analyzerId]) => this.isSelected(analyzerId))
        .flatMap(([, result]) => result.signals ?? []),
    );
  }

  private setSelected(selections: AnalysisSelection[], cancelAnalysis = true): void {
    if (cancelAnalysis && this.loadingAnalysis) {
      this.analysisRequest?.unsubscribe();
      this.analysisRequest = undefined;
      this.loadingAnalysis = false;
    }
    this.selectionStore.setSelections(selections);
  }
}
