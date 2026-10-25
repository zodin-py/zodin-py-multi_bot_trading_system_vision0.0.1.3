#!/usr/bin/env python3
"""
Tests for TradeExecutor — SL/TP calculation, position sizing,
max concurrent positions, cooldown enforcement, daily loss limit.
"""

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from unittest.mock import patch, MagicMock

from backend.execution.executor import TradeExecutor, Trade, TradeStatus, TradeSide
from backend.bots.base_bot import SignalType
from backend.indicators.provider import MockIndicatorProvider, _IndicatorFixture


# ---------- Fixtures ----------

@pytest.fixture
def executor(tmp_path):
    """Fresh executor with zero capital for predictable tests."""
    # Override the trades history file to use a temp file
    import backend.execution.executor as exec_module
    original_file = exec_module.TRADES_HISTORY_FILE
    temp_file = str(tmp_path / 'trades_test.json')
    exec_module.TRADES_HISTORY_FILE = temp_file
    try:
        ex = TradeExecutor(capital=10000.0)
        return ex
    finally:
        exec_module.TRADES_HISTORY_FILE = original_file


@pytest.fixture(autouse=True)
def force_testnet_for_tests(monkeypatch):
    """Keep tests isolated from any live-trading settings in the developer's .env."""
    from backend import config

    monkeypatch.setattr(config.config, 'USE_TESTNET', True)


@pytest.fixture
def mock_provider():
    return MockIndicatorProvider()


# ---------- SL/TP Calculation ----------

class TestDynamicSLTP:
    def test_long_sl_from_support(self, executor):
        """Long: SL should be nearest support below price within 2%."""
        entry = 100.0
        supports = [98.0, 95.0]   # 98 is within 2%
        resistances = [105.0]
        atr = 1.0

        sl, tp, src = executor.calculate_dynamic_sl_tp(
            'BTCUSDT', 'long', entry, supports, resistances, atr
        )
        assert sl == 98.0
        assert tp == 104.0  # 100 + (100-98)*2
        assert src == 'sr_level'

    def test_long_no_support_fallback_to_atr(self, executor):
        """Long: no support within 2% → ATR fallback."""
        entry = 100.0
        supports = [90.0]    # 10% away, too far
        resistances = [105.0]
        atr = 2.0

        sl, tp, src = executor.calculate_dynamic_sl_tp(
            'BTCUSDT', 'long', entry, supports, resistances, atr
        )
        assert src == 'atr_fallback'
        # SL = entry - atr = 98.0
        assert sl == pytest.approx(98.0, abs=0.01)
        # TP = entry + (entry - SL) * 2 = 100 + 2*2 = 104.0
        assert tp == pytest.approx(104.0, abs=0.01)

    def test_short_sl_from_resistance(self, executor):
        """Short: SL should be nearest resistance above price within 2%."""
        entry = 100.0
        supports = [95.0]
        resistances = [102.0, 105.0]  # 102 is within 2%

        sl, tp, src = executor.calculate_dynamic_sl_tp(
            'BTCUSDT', 'short', entry, supports, resistances, atr=1.0
        )
        assert sl == 102.0
        assert tp == 96.0  # 100 - (102-100)*2
        assert src == 'sr_level'

    def test_short_no_resistance_fallback(self, executor):
        entry = 100.0
        supports = [95.0]
        resistances = [110.0]  # 10% away
        atr = 1.5

        sl, tp, src = executor.calculate_dynamic_sl_tp(
            'BTCUSDT', 'short', entry, supports, resistances, atr
        )
        assert src == 'atr_fallback'
        # SL = entry + atr = 101.5
        assert sl == pytest.approx(101.5, abs=0.01)
        # TP = entry - (SL - entry) * 2 = 100 - 1.5*2 = 97.0
        assert tp == pytest.approx(97.0, abs=0.01)

    def test_empty_levels_fallback(self, executor):
        sl, tp, src = executor.calculate_dynamic_sl_tp(
            'BTCUSDT', 'long', 100.0, [], [], atr=1.0
        )
        assert src == 'atr_fallback'


# ---------- Position Sizing ----------

class TestPositionSizing:
    def test_basic_position_size(self, executor):
        """quantity = (capital * RISK_PERCENT / 100) / |entry - SL|"""
        executor.capital = 10000.0
        entry = 100.0
        sl = 98.0  # 2% risk
        qty = executor.calculate_position_size(entry, sl)
        # risk_amount = 10000 * 1.0 / 100 = 100
        # quantity = 100 / 2.0 = 50
        assert qty == 50.0

    def test_zero_sl_distance_returns_zero(self, executor):
        executor.capital = 10000.0
        qty = executor.calculate_position_size(100.0, 100.0)
        assert qty == 0.0

    def test_larger_risk_gives_smaller_quantity(self, executor):
        """Wider SL → smaller quantity for same risk amount."""
        executor.capital = 10000.0
        q1 = executor.calculate_position_size(100.0, 98.0)  # 2% risk
        q2 = executor.calculate_position_size(100.0, 99.0)  # 1% risk
        assert q2 > q1  # tighter SL = MORE quantity (more shares for same risk)


# ---------- Open Trade Guards ----------

class TestOpenTradeGuards:
    def test_holds_if_daily_loss_reached(self, executor):
        executor.daily_pnl = -15.0  # above MAX_DAILY_LOSS=10
        with patch.object(executor, '_place_order', return_value={'id': 'mock'}):
            result = executor.open_trade(
                'BTCUSDT', '1h', SignalType.BUY,
                entry_price=100.0,
                support_levels=[98.0],
                resistance_levels=[105.0],
                atr=1.0,
            )
        assert result is None

    def test_holds_if_cooldown_active(self, executor):
        import time
        executor._last_trade_time['BTCUSDT'] = time.time()
        with patch.object(executor, '_place_order', return_value={'id': 'mock'}):
            result = executor.open_trade(
                'BTCUSDT', '1h', SignalType.BUY,
                entry_price=100.0,
                support_levels=[98.0],
                atr=1.0,
            )
        assert result is None

    def test_holds_if_max_positions_reached(self, executor):
        # Pre-populate max positions
        for i in range(5):
            executor.open_trades[f'TRD{i:05d}'] = Trade(
                id=f'TRD{i:05d}', symbol='BTCUSDT', timeframe='1h',
                side='long', entry_price=100.0, quantity=1.0,
                stop_loss=98.0, take_profit=104.0,
                status=TradeStatus.OPEN, open_time=__import__('datetime').datetime.now(),
            )
        with patch.object(executor, '_place_order', return_value={'id': 'mock'}):
            result = executor.open_trade(
                'ETHUSDT', '1h', SignalType.BUY,
                entry_price=50.0, support_levels=[], atr=1.0,
            )
        assert result is None

    def test_rejects_invalid_signal(self, executor):
        result = executor.open_trade(
            'BTCUSDT', '1h', SignalType.HOLD,
            entry_price=100.0, support_levels=[], atr=1.0,
        )
        assert result is None


# ---------- Full Trade Flow (mocked ccxt) ----------

class TestFullTradeFlow:
    def test_open_and_close_long_trade(self, executor):
        """End-to-end: open long, close at higher price → positive P&L."""
        with patch.object(executor, '_place_order', return_value={'id': 'ord123'}):
            trade = executor.open_trade(
                'BTCUSDT', '1h', SignalType.BUY,
                entry_price=100.0,
                support_levels=[98.0],
                resistance_levels=[105.0],
                atr=1.0,
            )
        assert trade is not None
        assert trade.side == 'long'
        assert trade.stop_loss == 98.0
        assert trade.take_profit == 104.0
        assert trade.sl_source == 'sr_level'
        assert trade.id in executor.open_trades
        assert len(executor.open_trades) == 1

        # Close at profit
        closed = executor.close_trade(trade.id, current_price=103.0, reason='TP hit')
        assert closed is not None
        assert closed.status == TradeStatus.CLOSED
        assert closed.pnl > 0
        assert closed.notes == 'TP hit'
        assert trade.id not in executor.open_trades
        assert closed in executor.trade_history

    def test_close_long_at_loss(self, executor):
        with patch.object(executor, '_place_order', return_value={'id': 'ord1'}):
            trade = executor.open_trade(
                'BTCUSDT', '1h', SignalType.BUY,
                entry_price=100.0,
                support_levels=[98.0],
                atr=1.0,
            )
        closed = executor.close_trade(trade.id, current_price=97.0, reason='SL hit')
        assert closed.pnl < 0

    def test_open_and_close_short_trade(self, executor):
        with patch.object(executor, '_place_order', return_value={'id': 'ord2'}):
            trade = executor.open_trade(
                'BTCUSDT', '1h', SignalType.SELL,
                entry_price=100.0,
                resistance_levels=[102.0],
                atr=1.0,
            )
        assert trade.side == 'short'
        assert trade.stop_loss == 102.0
        assert trade.take_profit == 96.0

        closed = executor.close_trade(trade.id, current_price=97.0, reason='TP')
        assert closed.pnl > 0

    def test_check_trade_conditions_long_tp(self, executor):
        with patch.object(executor, '_place_order', return_value={'id': 'x'}):
            trade = executor.open_trade(
                'BTCUSDT', '1h', SignalType.BUY,
                entry_price=100.0, support_levels=[98.0], atr=1.0,
            )
        to_close = executor.check_trade_conditions('BTCUSDT', 104.5)
        assert trade.id in to_close

    def test_check_trade_conditions_long_sl(self, executor):
        with patch.object(executor, '_place_order', return_value={'id': 'x'}):
            trade = executor.open_trade(
                'BTCUSDT', '1h', SignalType.BUY,
                entry_price=100.0, support_levels=[98.0], atr=1.0,
            )
        to_close = executor.check_trade_conditions('BTCUSDT', 97.5)
        assert trade.id in to_close

    def test_check_trade_conditions_short_tp(self, executor):
        with patch.object(executor, '_place_order', return_value={'id': 'x'}):
            trade = executor.open_trade(
                'BTCUSDT', '1h', SignalType.SELL,
                entry_price=100.0, resistance_levels=[102.0], atr=1.0,
            )
        to_close = executor.check_trade_conditions('BTCUSDT', 95.0)
        assert trade.id in to_close

    def test_check_trade_conditions_short_sl(self, executor):
        with patch.object(executor, '_place_order', return_value={'id': 'x'}):
            trade = executor.open_trade(
                'BTCUSDT', '1h', SignalType.SELL,
                entry_price=100.0, resistance_levels=[102.0], atr=1.0,
            )
        to_close = executor.check_trade_conditions('BTCUSDT', 103.0)
        assert trade.id in to_close


# ---------- Cooldown ----------

class TestCooldown:
    def test_cooldown_prevents_immediate_retrade(self, executor):
        """After opening a trade, another for same symbol should be blocked."""
        with patch.object(executor, '_place_order', return_value={'id': 'a'}):
            t1 = executor.open_trade(
                'BTCUSDT', '1h', SignalType.BUY,
                entry_price=100.0, support_levels=[], atr=1.0,
            )
        assert t1 is not None
        # Immediately try again
        with patch.object(executor, '_place_order', return_value={'id': 'b'}):
            t2 = executor.open_trade(
                'BTCUSDT', '1h', SignalType.BUY,
                entry_price=100.0, support_levels=[], atr=1.0,
            )
        assert t2 is None  # cooldown active


# ---------- Daily Loss Limit ----------

class TestDailyLossLimit:
    def test_trading_halted_when_loss_exceeded(self, executor):
        executor.daily_pnl = -15.0
        assert executor._check_daily_loss_limit() is True

    def test_trading_allowed_when_under_limit(self, executor):
        executor.daily_pnl = -5.0
        assert executor._check_daily_loss_limit() is False

    def test_updated_limit_applies_to_existing_executor(self, executor, monkeypatch):
        from backend import config

        monkeypatch.setattr(config, 'MAX_DAILY_LOSS', 25.0)
        executor.daily_pnl = -20.0
        assert executor._check_daily_loss_limit() is False

        monkeypatch.setattr(config, 'MAX_DAILY_LOSS', 10.0)
        assert executor._check_daily_loss_limit() is True

    def test_capital_updated_on_close(self, executor):
        with patch.object(executor, '_place_order', return_value={'id': 'z'}):
            trade = executor.open_trade(
                'BTCUSDT', '1h', SignalType.BUY,
                entry_price=100.0, support_levels=[98.0], atr=1.0,
            )
        initial_capital = executor.capital
        executor.close_trade(trade.id, current_price=103.0)
        assert executor.capital > initial_capital


# ---------- Query Helpers ----------

class TestQueryHelpers:
    def test_get_open_trades(self, executor):
        assert len(executor.get_open_trades()) == 0

    def test_get_trade_history_empty(self, executor):
        assert executor.get_trade_history() == []

    def test_performance_stats_empty(self, executor):
        stats = executor.get_performance_stats()
        assert stats['total_trades'] == 0
        assert stats['win_rate'] == 0.0

    def test_portfolio(self, executor):
        with patch.object(executor, 'get_account_capital', return_value=10000.0):
            p = executor.get_portfolio()
        assert p['capital'] == 10000.0
        assert p['open_count'] == 0
        assert p['is_halted'] is False
        assert p['is_halted'] is False

    def test_get_account_capital_fetches_and_caches_binance_balance(self, executor, monkeypatch):
        from backend import config

        monkeypatch.setattr(config.config, 'BINANCE_API_KEY', 'test-key')
        monkeypatch.setattr(config.config, 'BINANCE_SECRET_KEY', 'test-secret')
        exchange = MagicMock()
        exchange.fetch_balance.return_value = {'total': {'USDT': 1234.56}}
        with patch.object(executor, '_create_exchange', return_value=exchange):
            assert executor.get_account_capital() == 1234.56
            assert executor.get_account_capital() == 1234.56

        exchange.fetch_balance.assert_called_once_with()
        exchange.close.assert_called_once_with()

    def test_get_account_capital_requires_api_keys(self, executor, monkeypatch):
        from backend import config

        monkeypatch.setattr(config.config, 'BINANCE_API_KEY', '')
        monkeypatch.setattr(config.config, 'BINANCE_SECRET_KEY', '')
        with pytest.raises(RuntimeError, match='API keys are not configured'):
            executor.get_account_capital()

    def test_get_account_capital_explains_invalid_timestamp(self, executor, monkeypatch):
        import ccxt
        from backend import config

        monkeypatch.setattr(config.config, 'BINANCE_API_KEY', 'test-key')
        monkeypatch.setattr(config.config, 'BINANCE_SECRET_KEY', 'test-secret')
        exchange = MagicMock()
        exchange.fetch_balance.side_effect = ccxt.InvalidNonce('invalid timestamp')
        with patch.object(executor, '_create_exchange', return_value=exchange):
            with pytest.raises(RuntimeError, match='synchronize Windows time'):
                executor.get_account_capital()

        exchange.close.assert_called_once_with()

    def test_live_trade_refreshes_capital_before_sizing(self, executor, monkeypatch):
        from backend import config

        monkeypatch.setattr(config.config, 'USE_TESTNET', False)
        with patch.object(executor, 'get_account_capital', return_value=500.0) as get_capital:
            with patch.object(executor, '_place_order', return_value={'id': 'live-order'}):
                trade = executor.open_trade(
                    'BTCUSDT', '1h', SignalType.BUY,
                    entry_price=100.0, support_levels=[98.0], atr=1.0,
                )

        assert trade is not None
        assert executor.capital == 500.0
        get_capital.assert_called_once_with()


# ---------- To/From Dict ----------

class TestTradeSerialization:
    def test_roundtrip(self):
        from datetime import datetime
        t = Trade(
            id='TRD00001', symbol='BTCUSDT', timeframe='1h',
            side='long', entry_price=100.0, quantity=50.0,
            stop_loss=98.0, take_profit=104.0,
            status=TradeStatus.OPEN, open_time=datetime.now(),
            sl_source='sr_level',
        )
        d = t.to_dict()
        t2 = Trade.from_dict(d)
        assert t2.id == t.id
        assert t2.stop_loss == t.stop_loss
        assert t2.take_profit == t.take_profit
        assert t2.sl_source == t.sl_source


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
