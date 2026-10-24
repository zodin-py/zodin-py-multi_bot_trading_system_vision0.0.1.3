"""Trade repository — JSON persistence for trades."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from backend.domains.execution.models import Trade, TradeStatus

logger = logging.getLogger(__name__)


class TradeRepository:
    """Persist trades to JSON file."""

    def __init__(self, filepath: str = 'trades/trades_history.json'):
        self._filepath = filepath
        self._trades: Dict[str, Trade] = {}
        self._history: List[Trade] = []
        self._load()

    def _load(self) -> None:
        """Load trades from JSON file."""
        if not os.path.exists(self._filepath):
            return
        try:
            with open(self._filepath, 'r') as f:
                data = json.load(f)
            for item in data.get('trades', []):
                trade = Trade.from_dict(item)
                if trade.status == TradeStatus.OPEN:
                    self._trades[trade.id] = trade
                else:
                    self._history.append(trade)
            logger.info(f"Loaded {len(self._trades)} open trades, {len(self._history)} closed trades")
        except Exception as e:
            logger.error(f"Failed to load trades: {e}")

    def _save(self) -> None:
        """Save all trades to JSON file."""
        try:
            all_trades = list(self._trades.values()) + self._history
            data = {
                'trades': [t.to_dict() for t in all_trades],
                'updated_at': datetime.now().isoformat(),
            }
            os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
            with open(self._filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save trades: {e}")

    def add_trade(self, trade: Trade) -> None:
        """Add or update a trade."""
        if trade.status == TradeStatus.OPEN:
            self._trades[trade.id] = trade
        else:
            if trade.id in self._trades:
                del self._trades[trade.id]
            self._history.append(trade)
        self._save()

    def get_open_trades(self) -> List[Trade]:
        """Get all open trades."""
        return list(self._trades.values())

    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Get a trade by ID."""
        return self._trades.get(trade_id)

    def get_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Trade]:
        """Get trade history with optional date filter."""
        trades = list(self._history)
        if start_date:
            trades = [t for t in trades if t.open_time >= start_date]
        if end_date:
            trades = [t for t in trades if t.open_time <= end_date]
        return trades
