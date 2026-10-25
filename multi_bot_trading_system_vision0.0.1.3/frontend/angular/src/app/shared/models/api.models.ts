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