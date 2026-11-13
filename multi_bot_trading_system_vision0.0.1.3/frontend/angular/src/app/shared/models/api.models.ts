// Mirror of the Flask backend response shapes (backend/app.py).
// Kept in one file so every component consumes the same contract.

export interface StatusResponse {
  status: 'running' | 'stopped';
  symbol: string;
  timeframe: string;
  timestamp: string;
}

export interface LoadCoinRequest {
  symbol: string;
  timeframe: string;
}

export interface LoadCoinResponse {
  success: boolean;
  symbol: string;
  timeframe: string;
  current_price: number;
  candles_loaded: number;
  error?: string;
}

export interface PriceResponse {
  symbol: string;
  price: number;
  timestamp: string;
}

export interface WalletBalance {
  asset: string;
  free: string;
  locked: string;
  usdt_value: number;
}

export interface WalletResponse {
  balances: WalletBalance[];
  total_usdt: number;
  timestamp: string;
}

export interface IndicatorsResponse {
  rsi: number[];
  macd: number[];
  ema: number[];
  timeframe: string;
  symbol: string;
}

export interface SettingsResponse {
  symbol: string;
  timeframe: string;
}

export interface AccountTrade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  price: number;
  amount: number;
  cost: number;
  timestamp: number;
  datetime: string;
  order: string | null;
  fee: { cost: number; currency: string } | null;
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  url: string;
  summary: string;
  date: string;
  kind: 'rss' | 'api' | 'x' | 'website';
  topics?: string[];
}

export interface NewsResponse {
  success: boolean;
  total_new: number;
  total_items: number;
  items: NewsItem[];
  error?: string;
}

// Candle data models for the coin selection chart feature

export interface CandleData {
  open_time: number;
  close_time: number;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  quote_volume: number;
  trades: number;
  taker_buy_base_volume: number;
  taker_buy_quote_volume: number;
}

export interface CandleChartData {
  success: boolean;
  symbol: string;
  timeframe: string;
  candle_count: number;
  candles: CandleData[];
  returned_count?: number;
  error?: string;
}

export interface CoinSelectionRequest {
  symbol: string;
  timeframe: string;
}

export interface CoinSelectionResponse {
  success: boolean;
  symbol: string;
  timeframe: string;
  candles_loaded: number;
  new_candles: number;
  duplicates_skipped: number;
  error?: string;
  message?: string;
}

export interface AvailableCoin {
  value: string;
  label: string;
}

export interface CoinsResponse {
  success: boolean;
  coins: string[];
  timeframes: Record<string, string>;
}

// --- Analysis System Models ---

export interface AnalyzerMetadata {
  id: string;
  name: string;
  category: 'indicator' | 'pattern' | 'strategy';
  description: string;
  icon: string;
  config_fields: string[];
  default_config?: Record<string, string | number | boolean>;
}

export interface AnalyzerCatalog {
  indicators: AnalyzerMetadata[];
  patterns: AnalyzerMetadata[];
  strategies: AnalyzerMetadata[];
}

export interface AnalysisSelection {
  analyzer_id: string;
  mode: 'current' | 'history';
  config: Record<string, string | number | boolean>;
}

export interface AnalysisRunRequest {
  symbol: string;
  timeframe: string;
  mode: 'current' | 'history';
  selected: AnalysisSelection[];
}

export interface AnalysisResult {
  status: 'success' | 'error' | 'no_signal';
  analyzer_id: string;
  symbol: string;
  timeframe: string;
  mode: 'current' | 'history';
  signals: AnalysisSignal[];
  series: unknown;
  error?: string;
}

export interface AnalysisSignal {
  timestamp: number;
  candle_index: number;
  type: string;
  direction: 'bullish' | 'bearish' | 'neutral';
  price: number;
  title: string;
  description: string;
  details?: Record<string, unknown>;
}

export interface RunAnalysisResponse {
  success?: boolean;
  symbol: string;
  timeframe: string;
  mode: 'current' | 'history';
  results: Record<string, AnalysisResult>;
  errors?: string | { analyzer_id: string; error: string }[];
}

export interface CandlestickPattern {
  body_ratio: number;
  lower_shadow_ratio: number;
  total_range: number;
  open: number;
  close: number;
  low: number;
  high: number;
}

export interface DojiDetails {
  body_ratio: number;
  total_range: number;
}