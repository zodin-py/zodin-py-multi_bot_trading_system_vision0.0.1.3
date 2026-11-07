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

export interface Trade {
  id: string;
  symbol: string;
  timeframe: string;
  side: 'long' | 'short';
  entry_price: number;
  quantity: number;
  stop_loss: number;
  take_profit: number;
  status: 'open' | 'closed';
  open_time: string;
  close_time: string | null;
  pnl: number;
  pnl_percent: number;
  notes: string;
  sl_source: string;
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
