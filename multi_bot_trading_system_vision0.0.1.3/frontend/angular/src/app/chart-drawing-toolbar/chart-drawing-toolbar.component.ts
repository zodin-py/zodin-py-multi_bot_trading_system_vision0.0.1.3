import {
  AfterViewInit,
  Component,
  ElementRef,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  type IChartApi,
  type ISeriesApi,
  type MouseEventParams,
  type Time,
  type UTCTimestamp,
} from 'lightweight-charts';

import { CandleData } from '../shared/models/api.models';

type DrawingTool =
  'select' | 'trendline' | 'horizontal' | 'fibonacci' | 'triangle' | 'long' | 'short' | 'rectangle';

interface DrawingAnchor {
  time: number;
  price: number;
}

interface ChartDrawing {
  id: string;
  tool: Exclude<DrawingTool, 'select'>;
  points: DrawingAnchor[];
}

interface ToolOption {
  id: Exclude<DrawingTool, 'select'>;
  label: string;
  icon: string;
}

interface DragState {
  drawingId: string;
  start: DrawingAnchor;
  original: DrawingAnchor[];
}

const DRAWING_STORAGE_PREFIX = 'multi-bot-chart-drawings-v1:';
const FAVORITES_STORAGE_KEY = 'multi-bot-chart-drawing-favorites-v1';
const FIBONACCI_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];

@Component({
  selector: 'app-chart-drawing-toolbar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './chart-drawing-toolbar.component.html',
  styleUrl: './chart-drawing-toolbar.component.css',
})
export class ChartDrawingToolbarComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() chart: IChartApi | null = null;
  @Input() series: ISeriesApi<'Candlestick'> | null = null;
  @Input() chartElement: HTMLElement | null = null;
  @Input() candles: CandleData[] = [];
  @Input() symbol = '';
  @ViewChild('drawingCanvas') private drawingCanvas?: ElementRef<HTMLCanvasElement>;

  readonly tools: ToolOption[] = [
    { id: 'trendline', label: 'Trend Line', icon: 'fa-chart-line' },
    { id: 'horizontal', label: 'Horizontal Line / Level', icon: 'fa-grip-lines' },
    { id: 'fibonacci', label: 'Fibonacci Retracement', icon: 'fa-ruler-combined' },
    { id: 'triangle', label: 'Geometric Pattern', icon: 'fa-draw-polygon' },
    { id: 'long', label: 'Long Position', icon: 'fa-arrow-up' },
    { id: 'short', label: 'Short Position', icon: 'fa-arrow-down' },
    { id: 'rectangle', label: 'Rectangle / Zone', icon: 'fa-square' },
  ];

  activeTool: DrawingTool = 'select';
  favorites: DrawingTool[] = ['trendline', 'horizontal'];
  favoritesOpen = false;
  magnetEnabled = false;
  drawingsVisible = true;
  selectedDrawingId: string | null = null;

  private drawings: ChartDrawing[] = [];
  private pendingPoints: DrawingAnchor[] = [];
  private previewAnchor: DrawingAnchor | null = null;
  private dragState: DragState | null = null;
  private boundChart: IChartApi | null = null;
  private boundChartElement: HTMLElement | null = null;
  private viewInitialized = false;

  get canUndo(): boolean {
    return this.drawings.length > 0 || this.pendingPoints.length > 0;
  }

  get canDelete(): boolean {
    return this.drawings.length > 0;
  }

  private readonly visibleRangeChanged = (): void => this.render();
  private readonly chartSizeChanged = (): void => this.resizeCanvas();
  private readonly chartClicked = (param: MouseEventParams<Time>): void => {
    if (this.activeTool !== 'select' || !param.point) return;
    this.selectedDrawingId = null;
    this.render();
  };
  private readonly pointerDownCapture = (event: PointerEvent): void => {
    if (this.activeTool !== 'select' || event.button !== 0 || !this.chartElement) return;

    const point = this.eventPoint(event);
    const drawing = this.findDrawingAt(point.x, point.y);
    this.selectedDrawingId = drawing?.id ?? null;
    if (!drawing) {
      this.render();
      return;
    }

    const start = this.anchorAt(point.x, point.y);
    if (!start) return;

    event.preventDefault();
    event.stopPropagation();
    this.dragState = {
      drawingId: drawing.id,
      start,
      original: drawing.points.map((anchor) => ({ ...anchor })),
    };
    this.chartElement.setPointerCapture(event.pointerId);
    this.render();
  };
  private readonly pointerMoveCapture = (event: PointerEvent): void => {
    if (!this.dragState) return;
    event.preventDefault();
    event.stopPropagation();

    const point = this.eventPoint(event);
    const current = this.anchorAt(point.x, point.y);
    if (!current) return;

    const drawing = this.drawings.find((item) => item.id === this.dragState?.drawingId);
    if (!drawing) return;
    const timeDelta = current.time - this.dragState.start.time;
    const priceDelta = current.price - this.dragState.start.price;
    const movedPoints = this.dragState.original.map((anchor) => ({
      time: anchor.time + timeDelta,
      price: anchor.price + priceDelta,
    }));
    drawing.points = this.magnetEnabled
      ? movedPoints.map((anchor) => this.snapToCandle(anchor))
      : movedPoints;
    this.render();
  };
  private readonly pointerUpCapture = (event: PointerEvent): void => {
    if (!this.dragState) return;
    event.preventDefault();
    event.stopPropagation();
    this.dragState = null;
    this.persistDrawings();
    this.render();
  };

  ngAfterViewInit(): void {
    this.viewInitialized = true;
    this.loadFavorites();
    this.loadDrawings();
    this.bindChart();
    this.resizeCanvas();
    this.render();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.viewInitialized) return;
    if (changes['chart'] || changes['chartElement']) this.bindChart();
    if (changes['symbol']) this.loadDrawings();
    if (changes['candles']) this.render();
    this.resizeCanvas();
  }

  ngOnDestroy(): void {
    this.unbindChart();
  }

  @HostListener('document:keydown.escape')
  cancelDrawingMode(): void {
    this.activeTool = 'select';
    this.pendingPoints = [];
    this.previewAnchor = null;
    this.favoritesOpen = false;
    this.render();
  }

  selectTool(tool: DrawingTool): void {
    this.activeTool = tool;
    this.pendingPoints = [];
    this.previewAnchor = null;
    this.favoritesOpen = false;
    this.selectedDrawingId = null;
    this.render();
  }

  toggleFavorites(): void {
    this.favoritesOpen = !this.favoritesOpen;
  }

  toggleFavorite(tool: DrawingTool): void {
    if (tool === 'select') return;
    this.favorites = this.favorites.includes(tool)
      ? this.favorites.filter((favorite) => favorite !== tool)
      : [...this.favorites, tool];
    this.persistFavorites();
  }

  toolLabel(tool: DrawingTool): string {
    return tool === 'select'
      ? 'Auswählen'
      : (this.tools.find((option) => option.id === tool)?.label ?? tool);
  }

  toggleMagnet(): void {
    this.magnetEnabled = !this.magnetEnabled;
  }

  toggleVisibility(): void {
    this.drawingsVisible = !this.drawingsVisible;
    this.render();
  }

  undo(): void {
    if (this.pendingPoints.length > 0) {
      this.pendingPoints.pop();
      this.previewAnchor = null;
    } else {
      const selectedIndex = this.drawings.findIndex(
        (drawing) => drawing.id === this.selectedDrawingId,
      );
      if (selectedIndex >= 0) {
        this.drawings.splice(selectedIndex, 1);
        this.selectedDrawingId = null;
      } else {
        this.drawings.pop();
      }
      this.persistDrawings();
    }
    this.render();
  }

  deleteDrawings(): void {
    if (this.drawings.length === 0) return;

    if (this.selectedDrawingId) {
      this.drawings = this.drawings.filter((drawing) => drawing.id !== this.selectedDrawingId);
      this.selectedDrawingId = null;
    } else if (window.confirm('Alle Zeichnungen für diesen Markt löschen?')) {
      this.drawings = [];
    } else {
      return;
    }

    this.persistDrawings();
    this.render();
  }

  onCanvasPointerDown(event: PointerEvent): void {
    if (this.activeTool === 'select') return;
    event.preventDefault();
    event.stopPropagation();

    const point = this.eventPoint(event);
    const anchor = this.anchorAt(point.x, point.y);
    if (!anchor) return;

    this.pendingPoints.push(this.magnetEnabled ? this.snapToCandle(anchor) : anchor);
    this.previewAnchor = null;

    if (this.activeTool === 'horizontal') {
      this.finishDrawing();
    } else if (this.pendingPoints.length === this.requiredPointCount(this.activeTool)) {
      this.finishDrawing();
    } else {
      this.render();
    }
  }

  onCanvasPointerMove(event: PointerEvent): void {
    if (this.activeTool === 'select' || this.pendingPoints.length === 0) return;
    const point = this.eventPoint(event);
    const anchor = this.anchorAt(point.x, point.y);
    if (!anchor) return;
    this.previewAnchor = this.magnetEnabled ? this.snapToCandle(anchor) : anchor;
    this.render();
  }

  private bindChart(): void {
    if (this.boundChart === this.chart && this.boundChartElement === this.chartElement) {
      return;
    }

    this.unbindChart();
    this.boundChart = this.chart;
    this.boundChartElement = this.chartElement;
    this.boundChart?.timeScale().subscribeVisibleLogicalRangeChange(this.visibleRangeChanged);
    this.boundChart?.timeScale().subscribeSizeChange(this.chartSizeChanged);
    this.boundChart?.subscribeClick(this.chartClicked);
    this.boundChartElement?.addEventListener('pointerdown', this.pointerDownCapture, true);
    this.boundChartElement?.addEventListener('pointermove', this.pointerMoveCapture, true);
    this.boundChartElement?.addEventListener('pointerup', this.pointerUpCapture, true);
    this.boundChartElement?.addEventListener('pointercancel', this.pointerUpCapture, true);
  }

  private unbindChart(): void {
    this.boundChart?.timeScale().unsubscribeVisibleLogicalRangeChange(this.visibleRangeChanged);
    this.boundChart?.timeScale().unsubscribeSizeChange(this.chartSizeChanged);
    this.boundChart?.unsubscribeClick(this.chartClicked);
    this.boundChartElement?.removeEventListener('pointerdown', this.pointerDownCapture, true);
    this.boundChartElement?.removeEventListener('pointermove', this.pointerMoveCapture, true);
    this.boundChartElement?.removeEventListener('pointerup', this.pointerUpCapture, true);
    this.boundChartElement?.removeEventListener('pointercancel', this.pointerUpCapture, true);
    this.boundChart = null;
    this.boundChartElement = null;
    this.dragState = null;
  }

  private resizeCanvas(): void {
    const canvas = this.drawingCanvas?.nativeElement;
    if (!canvas || !this.chart || !this.chartElement) return;

    const width = this.chart.timeScale().width();
    const height = this.chartElement.clientHeight;
    const pixelRatio = window.devicePixelRatio || 1;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    canvas.width = Math.round(width * pixelRatio);
    canvas.height = Math.round(height * pixelRatio);
    canvas.getContext('2d')?.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    this.render();
  }

  private render(): void {
    const canvas = this.drawingCanvas?.nativeElement;
    const context = canvas?.getContext('2d');
    if (!canvas || !context || !this.chart || !this.series) return;

    const pixelRatio = window.devicePixelRatio || 1;
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    context.clearRect(0, 0, canvas.width / pixelRatio, canvas.height / pixelRatio);

    if (this.drawingsVisible) {
      for (const drawing of this.drawings) {
        this.drawShape(context, drawing, drawing.id === this.selectedDrawingId);
      }
      this.drawPreview(context);
    }
  }

  private drawShape(
    context: CanvasRenderingContext2D,
    drawing: ChartDrawing,
    selected: boolean,
  ): void {
    const points = drawing.points.map((anchor) => this.coordinateFor(anchor));
    if (points.some((point) => point === null)) return;
    const coordinates = points.filter((point): point is { x: number; y: number } => point !== null);
    context.save();
    context.lineWidth = selected ? 2 : 1.5;
    context.strokeStyle = selected ? '#f8fafc' : '#38bdf8';
    context.fillStyle = 'rgba(56, 189, 248, 0.10)';
    context.setLineDash(selected ? [4, 3] : []);

    if (drawing.tool === 'trendline') {
      this.drawLine(context, coordinates[0], coordinates[1]);
    } else if (drawing.tool === 'horizontal') {
      context.beginPath();
      context.moveTo(0, coordinates[0].y);
      context.lineTo(this.chart?.timeScale().width() ?? 0, coordinates[0].y);
      context.stroke();
    } else if (drawing.tool === 'fibonacci') {
      this.drawFibonacci(context, coordinates[0], coordinates[1]);
    } else if (drawing.tool === 'rectangle') {
      this.drawRectangle(context, coordinates[0], coordinates[1]);
    } else if (drawing.tool === 'triangle') {
      context.beginPath();
      context.moveTo(coordinates[0].x, coordinates[0].y);
      context.lineTo(coordinates[1].x, coordinates[1].y);
      context.lineTo(coordinates[2].x, coordinates[2].y);
      context.closePath();
      context.fill();
      context.stroke();
    } else {
      this.drawPosition(context, coordinates);
    }

    context.restore();
  }

  private drawPreview(context: CanvasRenderingContext2D): void {
    if (this.pendingPoints.length === 0 || !this.previewAnchor || this.activeTool === 'select') {
      return;
    }

    const preview: ChartDrawing = {
      id: 'preview',
      tool: this.activeTool,
      points: [...this.pendingPoints, this.previewAnchor],
    };
    const required = this.requiredPointCount(this.activeTool);
    if (preview.points.length < required) {
      const first = this.coordinateFor(preview.points[0]);
      const last = this.coordinateFor(preview.points[preview.points.length - 1]);
      if (!first || !last) return;
      context.save();
      context.strokeStyle = '#7dd3fc';
      context.fillStyle = 'rgba(56, 189, 248, 0.08)';
      context.lineWidth = 1;
      context.setLineDash([4, 4]);
      if (this.activeTool === 'horizontal') {
        context.beginPath();
        context.moveTo(0, first.y);
        context.lineTo(this.chart?.timeScale().width() ?? 0, first.y);
        context.stroke();
      } else if (this.activeTool === 'rectangle') {
        this.drawRectangle(context, first, last);
      } else if (this.activeTool === 'fibonacci') {
        this.drawFibonacci(context, first, last);
      } else if (this.activeTool === 'long' || this.activeTool === 'short') {
        this.drawLine(context, first, last);
      } else {
        context.beginPath();
        context.moveTo(first.x, first.y);
        context.lineTo(last.x, last.y);
        context.stroke();
      }
      context.restore();
      return;
    }

    this.drawShape(context, preview, false);
  }

  private drawFibonacci(
    context: CanvasRenderingContext2D,
    start: { x: number; y: number },
    end: { x: number; y: number },
  ): void {
    for (const level of FIBONACCI_LEVELS) {
      const y = start.y + (end.y - start.y) * level;
      context.beginPath();
      context.moveTo(Math.min(start.x, end.x), y);
      context.lineTo(Math.max(start.x, end.x), y);
      context.stroke();
      context.fillStyle = '#cbd5e1';
      context.font = '10px Inter, sans-serif';
      context.fillText(`${(level * 100).toFixed(1)}%`, Math.max(start.x, end.x) + 4, y - 2);
      context.fillStyle = 'rgba(56, 189, 248, 0.10)';
    }
  }

  private drawRectangle(
    context: CanvasRenderingContext2D,
    start: { x: number; y: number },
    end: { x: number; y: number },
  ): void {
    const left = Math.min(start.x, end.x);
    const top = Math.min(start.y, end.y);
    const width = Math.abs(end.x - start.x);
    const height = Math.abs(end.y - start.y);
    context.fillRect(left, top, width, height);
    context.strokeRect(left, top, width, height);
  }

  private drawPosition(
    context: CanvasRenderingContext2D,
    points: Array<{ x: number; y: number }>,
  ): void {
    const [entry, stop, target] = points;
    const left = Math.min(entry.x, target.x);
    const width = Math.max(1, Math.abs(target.x - entry.x));

    context.fillStyle = 'rgba(34, 197, 94, 0.18)';
    context.fillRect(left, Math.min(entry.y, target.y), width, Math.abs(entry.y - target.y));
    context.fillStyle = 'rgba(239, 68, 68, 0.18)';
    context.fillRect(left, Math.min(entry.y, stop.y), width, Math.abs(entry.y - stop.y));
    context.strokeStyle = '#38bdf8';
    context.setLineDash([]);
    for (const point of [entry, stop, target]) {
      context.beginPath();
      context.moveTo(left, point.y);
      context.lineTo(left + width, point.y);
      context.stroke();
    }

    const risk = Math.abs(stop.y - entry.y);
    const reward = Math.abs(target.y - entry.y);
    const ratio = risk === 0 ? '—' : `${(reward / risk).toFixed(2)} R`;
    context.fillStyle = '#e2e8f0';
    context.font = '10px Inter, sans-serif';
    context.fillText(ratio, left + 4, Math.min(entry.y, target.y) + 12);
  }

  private drawLine(
    context: CanvasRenderingContext2D,
    start: { x: number; y: number },
    end: { x: number; y: number },
  ): void {
    context.beginPath();
    context.moveTo(start.x, start.y);
    context.lineTo(end.x, end.y);
    context.stroke();
  }

  private finishDrawing(): void {
    const tool = this.activeTool;
    const points = this.pendingPoints.map((anchor) => ({ ...anchor }));
    if (tool === 'horizontal') points.splice(1);
    if (tool === 'long' || tool === 'short') {
      const [entry, stop, target] = points;
      if (entry && stop && target) {
        points[0] = { ...entry };
        points[1] = { time: target.time, price: stop.price };
        points[2] = { ...target };
      }
    }
    if (tool !== 'select' && this.isDrawingTool(tool)) {
      this.drawings.push({
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        tool,
        points,
      });
      this.persistDrawings();
    }
    this.pendingPoints = [];
    this.previewAnchor = null;
    this.render();
  }

  private isDrawingTool(tool: DrawingTool): tool is ChartDrawing['tool'] {
    return tool !== 'select';
  }

  private requiredPointCount(tool: DrawingTool): number {
    if (tool === 'horizontal') return 1;
    if (tool === 'long' || tool === 'short' || tool === 'triangle') return 3;
    return 2;
  }

  private eventPoint(event: PointerEvent): { x: number; y: number } {
    const rect = this.drawingCanvas?.nativeElement.getBoundingClientRect();
    return {
      x: rect ? event.clientX - rect.left : 0,
      y: rect ? event.clientY - rect.top : 0,
    };
  }

  private anchorAt(x: number, y: number): DrawingAnchor | null {
    if (!this.chart || !this.series) return null;
    const time = this.chart.timeScale().coordinateToTime(x);
    const price = this.series.coordinateToPrice(y);
    if (typeof time !== 'number' || price === null) return null;
    return { time, price };
  }

  private coordinateFor(anchor: DrawingAnchor): { x: number; y: number } | null {
    if (!this.chart || !this.series) return null;
    const time = anchor.time as UTCTimestamp;
    const x =
      this.chart.timeScale().timeToCoordinate(time) ?? this.nearestCandleCoordinate(anchor.time);
    const y = this.series.priceToCoordinate(anchor.price);
    return x === null || x === undefined || y === null ? null : { x, y };
  }

  private nearestCandleCoordinate(timestamp: number): number | null {
    if (!this.chart || this.candles.length === 0) return null;
    const candleTimes = this.candles.map((candle) => candle.open_time / 1000);
    if (timestamp < Math.min(...candleTimes) || timestamp > Math.max(...candleTimes)) return null;
    let closest = this.candles[0];
    for (const candle of this.candles) {
      if (
        Math.abs(candle.open_time / 1000 - timestamp) <
        Math.abs(closest.open_time / 1000 - timestamp)
      ) {
        closest = candle;
      }
    }
    return this.chart
      .timeScale()
      .timeToCoordinate(Math.floor(closest.open_time / 1000) as UTCTimestamp);
  }

  private snapToCandle(anchor: DrawingAnchor): DrawingAnchor {
    if (this.candles.length === 0) return anchor;
    let closest = this.candles[0];
    for (const candle of this.candles) {
      if (
        Math.abs(candle.open_time / 1000 - anchor.time) <
        Math.abs(closest.open_time / 1000 - anchor.time)
      ) {
        closest = candle;
      }
    }
    const prices = [closest.open, closest.high, closest.low, closest.close];
    const price = prices.reduce((best, candidate) =>
      Math.abs(candidate - anchor.price) < Math.abs(best - anchor.price) ? candidate : best,
    );
    return { time: Math.floor(closest.open_time / 1000), price };
  }

  private findDrawingAt(x: number, y: number): ChartDrawing | null {
    if (!this.drawingsVisible) return null;
    for (let index = this.drawings.length - 1; index >= 0; index--) {
      const drawing = this.drawings[index];
      const points = drawing.points.map((anchor) => this.coordinateFor(anchor));
      if (points.some((point) => point === null)) continue;
      const coordinates = points.filter(
        (point): point is { x: number; y: number } => point !== null,
      );
      if (this.isNearDrawing(drawing.tool, coordinates, x, y)) return drawing;
    }
    return null;
  }

  private isNearDrawing(
    tool: ChartDrawing['tool'],
    points: Array<{ x: number; y: number }>,
    x: number,
    y: number,
  ): boolean {
    const first = points[0];
    const second = points[1];
    if (tool === 'horizontal') return Math.abs(y - first.y) <= 8;
    if (tool === 'trendline') return this.distanceToSegment(x, y, first, second) <= 8;
    if (tool === 'fibonacci') {
      return FIBONACCI_LEVELS.some(
        (level) =>
          x >= Math.min(first.x, second.x) - 6 &&
          x <= Math.max(first.x, second.x) + 6 &&
          Math.abs(y - (first.y + (second.y - first.y) * level)) <= 8,
      );
    }
    if (tool === 'rectangle' || tool === 'long' || tool === 'short') {
      const minX = Math.min(first.x, second.x);
      const maxX = Math.max(first.x, second.x);
      const minY = Math.min(first.y, second.y, points[2]?.y ?? second.y);
      const maxY = Math.max(first.y, second.y, points[2]?.y ?? second.y);
      return x >= minX && x <= maxX && y >= minY && y <= maxY;
    }
    return (
      this.distanceToSegment(x, y, first, second) <= 8 ||
      this.distanceToSegment(x, y, second, points[2]) <= 8 ||
      this.distanceToSegment(x, y, points[2], first) <= 8
    );
  }

  private distanceToSegment(
    x: number,
    y: number,
    start: { x: number; y: number },
    end: { x: number; y: number },
  ): number {
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const lengthSquared = dx * dx + dy * dy;
    const ratio =
      lengthSquared === 0
        ? 0
        : Math.max(0, Math.min(1, ((x - start.x) * dx + (y - start.y) * dy) / lengthSquared));
    return Math.hypot(x - (start.x + ratio * dx), y - (start.y + ratio * dy));
  }

  private loadDrawings(): void {
    this.drawings = [];
    this.selectedDrawingId = null;
    if (!this.symbol) {
      this.render();
      return;
    }

    try {
      const stored = localStorage.getItem(this.drawingStorageKey());
      if (stored) {
        const parsed: unknown = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          this.drawings = parsed.filter((item): item is ChartDrawing => this.isValidDrawing(item));
          if (this.drawings.length !== parsed.length) {
            console.warn(`Invalid chart drawings were ignored for ${this.symbol}`);
          }
        } else {
          console.warn(`Stored chart drawings have an invalid format for ${this.symbol}`);
        }
      }
    } catch (error) {
      console.error(`Chart drawings could not be loaded for ${this.symbol}`, error);
    }
    this.render();
  }

  private persistDrawings(): void {
    if (!this.symbol) return;
    try {
      localStorage.setItem(this.drawingStorageKey(), JSON.stringify(this.drawings));
    } catch (error) {
      console.error(`Chart drawings could not be saved for ${this.symbol}`, error);
    }
  }

  private drawingStorageKey(): string {
    return `${DRAWING_STORAGE_PREFIX}${encodeURIComponent(this.symbol)}`;
  }

  private isValidDrawing(value: unknown): value is ChartDrawing {
    if (typeof value !== 'object' || value === null) return false;
    const candidate = value as Partial<ChartDrawing>;
    const validTools: DrawingTool[] = [
      'trendline',
      'horizontal',
      'fibonacci',
      'triangle',
      'long',
      'short',
      'rectangle',
    ];
    return (
      typeof candidate.id === 'string' &&
      validTools.includes(candidate.tool as DrawingTool) &&
      Array.isArray(candidate.points) &&
      candidate.points.length === this.requiredPointCount(candidate.tool as DrawingTool) &&
      candidate.points.every(
        (point) =>
          typeof point?.time === 'number' &&
          Number.isFinite(point.time) &&
          typeof point.price === 'number' &&
          Number.isFinite(point.price),
      )
    );
  }

  private loadFavorites(): void {
    try {
      const stored = localStorage.getItem(FAVORITES_STORAGE_KEY);
      if (!stored) return;
      const parsed: unknown = JSON.parse(stored);
      if (!Array.isArray(parsed)) return;
      const allowedTools = new Set(this.tools.map((tool) => tool.id));
      this.favorites = parsed.filter(
        (tool): tool is DrawingTool =>
          typeof tool === 'string' && allowedTools.has(tool as ToolOption['id']),
      );
    } catch (error) {
      console.error('Chart drawing favorites could not be loaded', error);
    }
  }

  private persistFavorites(): void {
    try {
      localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(this.favorites));
    } catch (error) {
      console.error('Chart drawing favorites could not be saved', error);
    }
  }
}
