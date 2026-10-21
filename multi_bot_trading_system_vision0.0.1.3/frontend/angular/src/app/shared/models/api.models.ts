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

export interface BotProbabilities {
  [botName: string]: {
    buy: number;
    sell: number;
    hold: number;
    last_signal?: {
      signal_type: 'buy' | 'sell' | 'hold';
      timestamp: string;
    };
  };
}

export interface AggregatedSignal {
  final_signal: 'buy' | 'sell' | 'hold';
  confidence: number;
  buy_score: number;
  sell_score: number;
  hold_score: number;
}

export interface SignalsResponse {
  bot_probabilities: BotProbabilities;
  aggregated: AggregatedSignal;
  current_price: number;
}

export interface IndicatorsResponse {
  rsi: { value: number; signal: string; confidence: number };
  macd: { macd_line: number; signal_line: number; signal: string; confidence: number };
  mfi: { value: number; signal: string; confidence: number };
}

export interface Trade {
  trade_id?: string;
  id?: string;
  symbol: string;
  side: 'long' | 'short';
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  quantity?: number;
  status?: string;
  pnl?: number;
  pnl_percent?: number;
  close_time?: string;
}

export interface OpenTradesResponse {
  trades: Trade[];
  count: number;
}

export interface PortfolioResponse {
  capital: number;
  daily_pnl: number;
  open_count: number;
  is_halted: boolean;
  max_open_trades: number;
  trade_cooldown_sec: number;
}

export interface RiskLimitResponse {
  current_limit: number;
}

export interface RiskLimitSetResponse {
  success: boolean;
  current_limit: number;
}

export interface HistoryStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
}

export interface HistoryResponse {
  trades: Trade[];
  stats: HistoryStats;
}

export interface TradingActionResponse {
  status: 'started' | 'stopped';
}

export interface SettingsResponse {
  symbol: string;
  timeframe: string;
}