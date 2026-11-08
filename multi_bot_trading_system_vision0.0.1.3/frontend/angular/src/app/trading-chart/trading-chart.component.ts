import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type LogicalRange,
  type UTCTimestamp,
} from 'lightweight-charts';

import { CandleData } from '../shared/models/api.models';

@Component({
  selector: 'app-trading-chart',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './trading-chart.component.html',
  styleUrl: './trading-chart.component.css',
})
export class TradingChartComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() candles: CandleData[] = [];
  @Input() symbol = '';
  @Input() timeframe = '';
  @ViewChild('chartContainer', { static: true })
  private chartContainer!: ElementRef<HTMLDivElement>;

  constructor(private readonly changeDetector: ChangeDetectorRef) {}

  chartReady = false;
  autoScale = true;
  activeCandle: CandleData | null = null;

  private chart?: IChartApi;
  private candleSeries?: ISeriesApi<'Candlestick'>;
  private volumeSeries?: ISeriesApi<'Histogram'>;
  private currentPriceLine?: ReturnType<ISeriesApi<'Candlestick'>['createPriceLine']>;
  private renderedCandles: CandleData[] = [];
  private renderedSymbol = '';
  private renderedTimeframe = '';

  ngAfterViewInit(): void {
    this.updateData();
  }

  ngOnChanges(_changes: SimpleChanges): void {
    this.updateData();
  }

  ngOnDestroy(): void {
    this.chart?.remove();
    this.chart = undefined;
  }

  zoomIn(): void {
    this.changeBarSpacing(1.25);
  }

  zoomOut(): void {
    this.changeBarSpacing(0.8);
  }

  goToLive(): void {
    this.chart?.timeScale().scrollToRealTime();
  }

  resetView(): void {
    this.autoScale = true;
    this.chart?.priceScale('right').applyOptions({ autoScale: true });
    this.chart?.timeScale().fitContent();
  }

  toggleAutoScale(): void {
    this.autoScale = !this.autoScale;
    this.chart?.priceScale('right').applyOptions({ autoScale: this.autoScale });
  }

  handleDoubleClick(event: MouseEvent): void {
    const bounds = this.chartContainer.nativeElement.getBoundingClientRect();
    if (event.clientX >= bounds.right - 76) {
      this.autoScale = true;
      this.chart?.priceScale('right').applyOptions({ autoScale: true });
      return;
    }

    this.resetView();
  }

  private createChart(): void {
    this.chart = createChart(this.chartContainer.nativeElement, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: '#0b1220' },
        textColor: '#94a3b8',
        fontFamily: 'Inter, Segoe UI, sans-serif',
        panes: {
          separatorColor: '#1e293b',
          separatorHoverColor: '#334155',
        },
      },
      grid: {
        vertLines: { color: 'rgba(51, 65, 85, 0.35)' },
        horzLines: { color: 'rgba(51, 65, 85, 0.35)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#94a3b8', width: 1, style: 2, labelBackgroundColor: '#334155' },
        horzLine: { color: '#94a3b8', width: 1, style: 2, labelBackgroundColor: '#334155' },
      },
      rightPriceScale: {
        borderColor: '#334155',
        autoScale: true,
        scaleMargins: { top: 0.08, bottom: 0.25 },
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 8,
        shiftVisibleRangeOnNewBar: false,
      },
      handleScroll: {
        mouseWheel: false,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        mouseWheel: true,
        axisPressedMouseMove: { time: true, price: true },
        pinch: true,
      },
    });

    this.candleSeries = this.chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      priceLineVisible: false,
      lastValueVisible: true,
    });

    this.volumeSeries = this.chart.addSeries(HistogramSeries, {
      priceScaleId: 'volume',
      priceFormat: { type: 'volume' },
      lastValueVisible: false,
      priceLineVisible: false,
    });
    this.chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
      visible: false,
    });

    this.chart.subscribeCrosshairMove((param) => {
      const candle = this.candleSeries ? param.seriesData.get(this.candleSeries) : undefined;
      if (candle && 'open' in candle && 'high' in candle && 'low' in candle && 'close' in candle) {
        this.activeCandle =
          this.candles.find((item) => Math.floor(item.open_time / 1000) === Number(candle.time)) ??
          null;
      } else if (!param.time) {
        this.activeCandle = this.candles[this.candles.length - 1] ?? null;
      }
      this.changeDetector.markForCheck();
    });
    this.chartReady = true;
  }

  private updateData(): void {
    if (!this.chart && this.candles.length > 0) this.createChart();
    if (!this.chart || !this.candleSeries || !this.volumeSeries) return;

    const contextChanged =
      this.renderedSymbol !== this.symbol || this.renderedTimeframe !== this.timeframe;
    if (contextChanged || this.renderedCandles.length === 0) {
      this.setAllData();
      this.chart.timeScale().fitContent();
      this.chart.timeScale().scrollToRealTime();
      return;
    }

    const newestRendered = this.renderedCandles[this.renderedCandles.length - 1];
    const newCandles = this.candles.filter((candle) => candle.open_time > newestRendered.open_time);
    if (newCandles.length === 0) return;

    const visibleRange = this.chart.timeScale().getVisibleLogicalRange();
    const wasFollowingLive = this.isAtLiveEdge(visibleRange);
    for (const candle of newCandles) {
      this.candleSeries.update(this.toCandlePoint(candle));
      this.volumeSeries.update(this.toVolumePoint(candle));
    }

    const totalLength = this.renderedCandles.length + newCandles.length;
    if (totalLength > 1000) {
      this.setAllData();
      if (visibleRange) {
        const offset = this.renderedCandles.length - totalLength;
        this.restoreVisibleRange(visibleRange, wasFollowingLive, offset);
      }
    } else {
      this.renderedCandles = [...this.renderedCandles, ...newCandles];
      this.updatePriceLine();
      if (visibleRange) this.restoreVisibleRange(visibleRange, wasFollowingLive, 0);
    }
    this.activeCandle = this.candles[this.candles.length - 1] ?? null;
  }

  private setAllData(): void {
    this.renderedCandles = this.candles.slice(-1000);
    this.renderedSymbol = this.symbol;
    this.renderedTimeframe = this.timeframe;
    this.candleSeries?.setData(this.renderedCandles.map((candle) => this.toCandlePoint(candle)));
    this.volumeSeries?.setData(this.renderedCandles.map((candle) => this.toVolumePoint(candle)));
    this.activeCandle = this.renderedCandles[this.renderedCandles.length - 1] ?? null;
    this.updatePriceLine();
  }

  private updatePriceLine(): void {
    if (!this.candleSeries || this.renderedCandles.length === 0) return;
    if (this.currentPriceLine) this.candleSeries.removePriceLine(this.currentPriceLine);

    const lastCandle = this.renderedCandles[this.renderedCandles.length - 1];
    const bullish = lastCandle.close >= lastCandle.open;
    this.currentPriceLine = this.candleSeries.createPriceLine({
      price: lastCandle.close,
      color: bullish ? '#22c55e' : '#ef4444',
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
      title: 'Last',
    });
  }

  private changeBarSpacing(factor: number): void {
    const timeScale = this.chart?.timeScale();
    if (!timeScale) return;
    const currentSpacing = timeScale.options().barSpacing;
    timeScale.applyOptions({ barSpacing: Math.max(2, Math.min(40, currentSpacing * factor)) });
  }

  private isAtLiveEdge(range: LogicalRange | null): boolean {
    return range !== null && range.to >= this.renderedCandles.length - 2;
  }

  private restoreVisibleRange(range: LogicalRange, wasFollowingLive: boolean, offset: number): void {
    if (wasFollowingLive) {
      this.chart?.timeScale().scrollToRealTime();
      return;
    }
    this.chart?.timeScale().setVisibleLogicalRange({
      from: range.from + offset,
      to: range.to + offset,
    });
  }

  private toCandlePoint(candle: CandleData) {
    return {
      time: Math.floor(candle.open_time / 1000) as UTCTimestamp,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    };
  }

  private toVolumePoint(candle: CandleData) {
    return {
      time: Math.floor(candle.open_time / 1000) as UTCTimestamp,
      value: candle.volume,
      color: candle.close >= candle.open ? 'rgba(34, 197, 94, 0.35)' : 'rgba(239, 68, 68, 0.35)',
    };
  }
}
