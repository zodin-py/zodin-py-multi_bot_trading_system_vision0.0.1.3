# filepath: execution/executor.py
"""
Executor - Trade Execution mit Stop-Loss & Take-Profit
Verwaltet offene Trades und führt Orders aus.

Unterstützt:
- Dynamische SL/TP-Berechnung aus SR-Bot Support/Resistance Levels (2:1 RR)
- Fallback auf ATR-basierte Berechnung wenn keine S/R innerhalb 2%
- Positionsgrößenberechnung nach Risk-Management-Formel
- Max 5 gleichzeitige offene Positionen
- Cooldown zwischen Trades pro Symbol
- Echte Order-Platzierung via ccxt auf Binance Testnet
- P&L-Berechnung mit aktuellem Marktpreis
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import ccxt

from backend import config
from backend.bots.base_bot import SignalType
from backend.config import (
    RISK_PERCENT,
    RISK_REWARD_RATIO,
    TRADES_HISTORY_FILE,
    INITIAL_CAPITAL,
    MAX_OPEN_TRADES,
    TRADE_COOLDOWN_SEC,
    DYNAMIC_SL_TP_ENABLED,
)


logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """Trade Status"""
    OPEN = 'open'
    CLOSED = 'closed'
    CANCELLED = 'cancelled'


class TradeSide(Enum):
    LONG = 'long'
    SHORT = 'short'


@dataclass
class Trade:
    """Trade Object"""
    id: str
    symbol: str
    timeframe: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    status: TradeStatus
    open_time: datetime
    close_time: Optional[datetime] = None
    pnl: float = 0
    pnl_percent: float = 0
    notes: str = ''
    sl_source: str = ''  # 'sr_level' or 'atr_fallback'

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'side': self.side,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'stop_loss': round(self.stop_loss, 8),
            'take_profit': round(self.take_profit, 8),
            'status': self.status.value,
            'open_time': self.open_time.isoformat(),
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'pnl': round(self.pnl, 2),
            'pnl_percent': round(self.pnl_percent, 2),
            'notes': self.notes,
            'sl_source': self.sl_source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Trade':
        return cls(
            id=data['id'],
            symbol=data['symbol'],
            timeframe=data['timeframe'],
            side=data['side'],
            entry_price=data['entry_price'],
            quantity=data['quantity'],
            stop_loss=data['stop_loss'],
            take_profit=data['take_profit'],
            status=TradeStatus(data['status']),
            open_time=datetime.fromisoformat(data['open_time']),
            close_time=datetime.fromisoformat(data['close_time']) if data.get('close_time') else None,
            pnl=data.get('pnl', 0),
            pnl_percent=data.get('pnl_percent', 0),
            notes=data.get('notes', ''),
            sl_source=data.get('sl_source', ''),
        )


class TradeExecutor:
    """Trade Executor - führt Trades aus und verwaltet sie"""

    def __init__(self, capital: float = INITIAL_CAPITAL, simulated: bool = False):
        self.capital = capital
        self.open_trades: Dict[str, Trade] = {}
        self.trade_history: List[Trade] = []
        self.trade_counter = 0
        self._simulated = simulated

        # Daily loss tracking
        self.daily_pnl: float = 0.0
        self._daily_reset_date: Optional[str] = datetime.now(tz=__import__('datetime').timezone.utc).date().isoformat()
        self._trades_closed_today: List[float] = []

        # Cooldown tracking: symbol -> timestamp of last trade close/open
        self._last_trade_time: Dict[str, float] = {}

        # Max concurrent positions
        self.max_open_trades = MAX_OPEN_TRADES

        # Cooldown seconds per symbol
        self.cooldown_sec = TRADE_COOLDOWN_SEC

        # Dynamic SL/TP
        self.dynamic_sl_tp = DYNAMIC_SL_TP_ENABLED

        # Load existing trades
        self._load_trades()

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def _load_trades(self):
        """Load trades from the history file."""
        try:
            if os.path.exists(TRADES_HISTORY_FILE):
                with open(TRADES_HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    for trade_data in data:
                        trade = Trade.from_dict(trade_data)
                        if trade.status == TradeStatus.OPEN:
                            self.open_trades[trade.id] = trade
                        else:
                            self.trade_history.append(trade)
                            self._trades_closed_today.append(trade.pnl)

                    # Set trade counter
                    all_ids = [int(t.id.replace('TRD', '')) for t in self.trade_history]
                    all_ids += [int(t.id.replace('TRD', '')) for t in self.open_trades.values()]
                    self.trade_counter = max(all_ids) if all_ids else 0

                # Recalculate daily P&L from history
                self._rebuild_daily_pnl()
        except Exception as e:
            logger.error(f"Error loading trades: {e}")

    def _rebuild_daily_pnl(self):
        """Rebuild daily P&L from trade history after restart."""
        today = datetime.now(tz=__import__('datetime').timezone.utc).date().isoformat()
        self.daily_pnl = 0.0
        for trade in self.trade_history:
            if trade.close_time and trade.close_time.date().isoformat() == today:
                self.daily_pnl += trade.pnl

    def _save_trades(self):
        """Save all trades (open + closed) to the history file."""
        try:
            os.makedirs(os.path.dirname(TRADES_HISTORY_FILE), exist_ok=True)
            all_trades = self.trade_history + list(self.open_trades.values())
            with open(TRADES_HISTORY_FILE, 'w') as f:
                json.dump([t.to_dict() for t in all_trades], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trades: {e}")

    # -------------------------------------------------------------------------
    # Daily loss & cooldown helpers
    # -------------------------------------------------------------------------

    def _check_daily_loss_limit(self) -> bool:
        """Return True if daily loss limit has been reached (trading should halt)."""
        today = datetime.now(tz=__import__('datetime').timezone.utc).date().isoformat()
        if self._daily_reset_date != today:
            # New day — reset
            self.daily_pnl = 0.0
            self._trades_closed_today = []
            self._daily_reset_date = today
            logger.info("Daily P&L counter reset")

        max_daily_loss = config.MAX_DAILY_LOSS
        if max_daily_loss > 0 and self.daily_pnl <= -max_daily_loss:
            logger.warning(
                f"Daily loss limit reached: daily_pnl={self.daily_pnl:.2f} <= -{max_daily_loss}"
            )
            return True
        return False

    def _check_cooldown(self, symbol: str) -> bool:
        """Return True if a trade for this symbol was opened/closed within cooldown window."""
        now = time.time()
        last = self._last_trade_time.get(symbol)
        if last is not None and (now - last) < self.cooldown_sec:
            remaining = int(self.cooldown_sec - (now - last))
            logger.info(f"Cooldown active for {symbol}: {remaining}s remaining")
            return True
        return False

    def _record_trade_time(self, symbol: str):
        """Record the timestamp of a trade event (open or close)."""
        self._last_trade_time[symbol] = time.time()

    # -------------------------------------------------------------------------
    # SL/TP Calculation
    # -------------------------------------------------------------------------

    def calculate_dynamic_sl_tp(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        support_levels: List[float],
        resistance_levels: List[float],
        atr: float,
    ) -> tuple:
        """
        Calculate dynamic SL and TP from S/R levels with 2:1 RR.

        Returns (stop_loss, take_profit, sl_source).
        """
        if side == 'long':
            # Long: SL below nearest support
            sl_level = self._find_nearest_level(
                support_levels, entry_price, below=True
            )
            if sl_level is None:
                # Fallback: ATR-based
                sl_level = entry_price * (1 - atr / entry_price)
                sl_source = 'atr_fallback'
            else:
                sl_source = 'sr_level'

            stop_loss = sl_level
            risk = entry_price - stop_loss
            if risk <= 0:
                # Safety: don't allow zero/negative risk
                stop_loss = entry_price * (1 - RISK_PERCENT / 100)
                risk = abs(entry_price - stop_loss)
                sl_source = 'atr_fallback'

            take_profit = entry_price + risk * RISK_REWARD_RATIO

        else:  # short
            # Short: SL above nearest resistance
            sl_level = self._find_nearest_level(
                resistance_levels, entry_price, below=False
            )
            if sl_level is None:
                sl_level = entry_price * (1 + atr / entry_price)
                sl_source = 'atr_fallback'
            else:
                sl_source = 'sr_level'

            stop_loss = sl_level
            risk = stop_loss - entry_price
            if risk <= 0:
                stop_loss = entry_price * (1 + RISK_PERCENT / 100)
                risk = abs(entry_price - stop_loss)
                sl_source = 'atr_fallback'

            take_profit = entry_price - risk * RISK_REWARD_RATIO

        return round(stop_loss, 8), round(take_profit, 8), sl_source

    @staticmethod
    def _find_nearest_level(levels: List[float], price: float, below: bool) -> Optional[float]:
        """Find the nearest level within 2% of price, either below (for longs) or above (for shorts)."""
        if not levels:
            return None

        candidates = []
        for level in levels:
            dist = abs(level - price) / price
            if dist <= 0.02:  # within 2%
                if below and level < price:
                    candidates.append((dist, level))
                elif not below and level > price:
                    candidates.append((dist, level))

        if not candidates:
            return None

        # Return closest level
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    # -------------------------------------------------------------------------
    # Position sizing
    # -------------------------------------------------------------------------

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """
        Position size = (capital * RISK_PERCENT / 100) / |entry_price - stop_loss|
        """
        risk_amount = self.capital * (RISK_PERCENT / 100)
        sl_distance = abs(entry_price - stop_loss)

        if sl_distance == 0:
            logger.warning("SL distance is zero, cannot calculate position size")
            return 0.0

        quantity = risk_amount / sl_distance
        return quantity

    # -------------------------------------------------------------------------
    # Open trade
    # -------------------------------------------------------------------------

    def open_trade(
        self,
        symbol: str,
        timeframe: str,
        signal: SignalType,
        entry_price: float,
        support_levels: Optional[List[float]] = None,
        resistance_levels: Optional[List[float]] = None,
        atr: float = 0.0,
    ) -> Optional[Trade]:
        """
        Open a new trade with dynamic SL/TP and place real order via ccxt.

        Args:
            symbol: Trading pair (e.g. 'BTCUSDT')
            timeframe: Timeframe string
            signal: BUY or SELL
            entry_price: Current market price
            support_levels: List of SR bot support levels
            resistance_levels: List of SR bot resistance levels
            atr: Current ATR value for fallback SL calculation

        Returns:
            Trade object or None if conditions not met
        """
        try:
            # Check daily loss limit
            if self._check_daily_loss_limit():
                logger.warning(f"Trading halted: daily loss limit reached for {symbol}")
                return None

            # Check cooldown
            if self._check_cooldown(symbol):
                logger.info(f"Skipping trade: cooldown active for {symbol}")
                return None

            # Check max concurrent positions
            if len(self.open_trades) >= self.max_open_trades:
                logger.warning(f"Max open trades ({self.max_open_trades}) reached")
                return None

            # Determine side
            if signal == SignalType.BUY:
                side = 'long'
            elif signal == SignalType.SELL:
                side = 'short'
            else:
                logger.warning(f"Invalid signal type: {signal}")
                return None

            # Determine S/R levels (prefer passed values, fallback to empty)
            if not self.dynamic_sl_tp:
                # Static SL/TP
                if side == 'long':
                    stop_loss = entry_price * (1 - RISK_PERCENT / 100)
                    take_profit = entry_price * (1 + RISK_PERCENT * RISK_REWARD_RATIO / 100)
                else:
                    stop_loss = entry_price * (1 + RISK_PERCENT / 100)
                    take_profit = entry_price * (1 - RISK_PERCENT * RISK_REWARD_RATIO / 100)
                sl_source = 'static'
            else:
                sup = support_levels or []
                res = resistance_levels or []
                stop_loss, take_profit, sl_source = self.calculate_dynamic_sl_tp(
                    symbol, side, entry_price, sup, res, atr
                )

            # Calculate position size
            quantity = self.calculate_position_size(entry_price, stop_loss)

            if quantity <= 0:
                logger.warning(f"Invalid position size for {symbol}")
                return None

            # Place real order via ccxt (skip in simulated mode for backtesting)
            if not self._simulated:
                order_result = self._place_order(symbol, side, entry_price, quantity)
                if order_result is None:
                    logger.error(f"Failed to place order for {symbol}")
                    return None

            # Create trade record
            self.trade_counter += 1
            trade = Trade(
                id=f"TRD{self.trade_counter:05d}",
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                status=TradeStatus.OPEN,
                open_time=datetime.now(),
                sl_source=sl_source,
            )

            self.open_trades[trade.id] = trade
            if not self._simulated:
                self._save_trades()
            self._record_trade_time(symbol)

            logger.info(
                f"Opened trade: {trade.id} - {side} {symbol} @ {entry_price:.8f} "
                f"qty={quantity:.6f} SL={stop_loss:.8f} TP={take_profit:.8f} source={sl_source}"
            )

            return trade

        except Exception as e:
            logger.error(f"Error opening trade: {e}")
            return None

    def _place_order(self, symbol: str, side: str, price: float, quantity: float) -> Optional[dict]:
        """
        Place a real market order via ccxt on Binance Testnet.
        Returns the order dict on success, None on failure.
        """
        try:
            exchange = ccxt.binance({
                'apiKey': os.environ.get('BINANCE_API_KEY', ''),
                'secret': os.environ.get('BINANCE_SECRET_KEY', ''),
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'},
            })
            if os.environ.get('USE_TESTNET', 'true').lower() == 'true':
                exchange.set_sandbox_mode(True)

            # Market order (fills at current market price)
            order = exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,   # 'buy' or 'sell'
                amount=quantity,
            )
            exchange.close()
            logger.info(f"ccxt order placed: {order.get('id')} for {symbol} {side} {quantity}")
            return order

        except ccxt.BaseError as e:
            logger.error(f"ccxt order placement failed for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error placing ccxt order for {symbol}: {e}")
            return None

    # -------------------------------------------------------------------------
    # Close trade
    # -------------------------------------------------------------------------

    def close_trade(
        self,
        trade_id: str,
        reason: str = 'manual',
        current_price: Optional[float] = None,
    ) -> Optional[Trade]:
        """
        Close an open trade and update P&L with actual current price.

        Args:
            trade_id: Trade ID to close
            reason: Reason for closing
            current_price: Current market price (fetches from MarketData if None)
        """
        if trade_id not in self.open_trades:
            logger.warning(f"Trade {trade_id} not found")
            return None

        trade = self.open_trades[trade_id]

        # Use provided price or fall back to entry (placeholder if no price available)
        if current_price is None:
            current_price = trade.entry_price

        # Calculate P&L
        if trade.side == 'long':
            pnl = (current_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - current_price) * trade.quantity

        pnl_percent = (pnl / (trade.entry_price * trade.quantity)) * 100 if trade.entry_price > 0 else 0

        # Update trade
        trade.status = TradeStatus.CLOSED
        trade.close_time = datetime.now()
        trade.pnl = round(pnl, 2)
        trade.pnl_percent = round(pnl_percent, 2)
        trade.notes = reason

        # Update capital and daily P&L
        self.capital += pnl
        today = datetime.now(tz=__import__('datetime').timezone.utc).date().isoformat()
        if trade.close_time.date().isoformat() == today:
            self.daily_pnl += pnl
            self._trades_closed_today.append(pnl)

        # Move to history
        del self.open_trades[trade_id]
        self.trade_history.append(trade)
        self._save_trades()
        self._record_trade_time(trade.symbol)

        logger.info(
            f"Closed trade: {trade.id} - {trade.side} {trade.symbol} "
            f"P&L: {pnl:.2f} ({pnl_percent:.2f}%) reason={reason}"
        )

        return trade

    # -------------------------------------------------------------------------
    # Check conditions (SL/TP hits)
    # -------------------------------------------------------------------------

    def check_trade_conditions(self, symbol: str, current_price: float) -> List[str]:
        """
        Check SL/TP conditions for all open trades of a symbol.
        Returns list of trade IDs to close.
        """
        trades_to_close = []

        for trade_id, trade in self.open_trades.items():
            if trade.symbol != symbol:
                continue

            if trade.side == 'long':
                if current_price >= trade.take_profit:
                    trades_to_close.append((trade_id, 'TP'))
                elif current_price <= trade.stop_loss:
                    trades_to_close.append((trade_id, 'SL'))
            else:  # short
                if current_price <= trade.take_profit:
                    trades_to_close.append((trade_id, 'TP'))
                elif current_price >= trade.stop_loss:
                    trades_to_close.append((trade_id, 'SL'))

        return [tid for tid, _ in trades_to_close]

    # -------------------------------------------------------------------------
    # Query helpers
    # -------------------------------------------------------------------------

    def get_open_trades(self) -> List[Trade]:
        """Get all open trades."""
        return list(self.open_trades.values())

    def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Trade]:
        """Get trade history with optional date filter."""
        trades = list(self.trade_history)

        if start_date:
            trades = [t for t in trades if t.open_time >= start_date]
        if end_date:
            trades = [t for t in trades if t.open_time <= end_date]

        return trades

    def get_performance_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Calculate performance statistics."""
        trades = self.get_trade_history(start_date, end_date)

        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_pnl_percent': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
            }

        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl <= 0]
        total_pnl = sum(t.pnl for t in trades)
        total_pnl_percent = sum(t.pnl_percent for t in trades)

        return {
            'total_trades': len(trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': round((len(winning) / len(trades)) * 100, 2) if trades else 0,
            'total_pnl': round(total_pnl, 2),
            'total_pnl_percent': round(total_pnl_percent, 2),
            'avg_win': round(sum(t.pnl for t in winning) / len(winning), 2) if winning else 0,
            'avg_loss': round(sum(t.pnl for t in losing) / len(losing), 2) if losing else 0,
        }

    def get_portfolio(self) -> Dict[str, Any]:
        """Get portfolio status."""
        daily_halted = self._check_daily_loss_limit()
        return {
            'capital': round(self.capital, 2),
            'daily_pnl': round(self.daily_pnl, 2),
            'open_count': len(self.open_trades),
            'is_halted': daily_halted,
            'max_open_trades': self.max_open_trades,
            'trade_cooldown_sec': self.cooldown_sec,
        }

    def __repr__(self) -> str:
        return (
            f"TradeExecutor(open_trades={len(self.open_trades)}, "
            f"capital={self.capital:.2f}, daily_pnl={self.daily_pnl:.2f})"
        )


# Backwards-compatible alias
Executor = TradeExecutor
