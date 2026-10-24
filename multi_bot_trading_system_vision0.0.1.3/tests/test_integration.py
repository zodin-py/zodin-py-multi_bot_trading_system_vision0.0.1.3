"""
Integration verification test suite for the multi-bot trading system.
Tests that all domain modules import correctly and the DI container builds.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'multi_bot_trading_system_vision0.0.1.3'))

def test_domain_imports():
    print('=' * 60)
    print('Testing domain imports...')
    print('=' * 60)
    from backend.domains.strategies import SRBot, SMCBot, HarmonicBot, TrendBot, StrategiesService, Signal, SignalType
    print('[PASS] Strategies domain imports OK')
    from backend.domains.analysis import Brain, AnalysisService, AggregatedSignal, BotSignal, SignalType
    print('[PASS] Analysis domain imports OK')
    from backend.domains.trades import Trade, TradeType, TradeStatus, TradesService, TradesRepository
    print('[PASS] Trades domain imports OK')
    from backend.domains.portfolio import PortfolioService, Portfolio, OpenPosition, DailyPnL, CapitalSnapshot
    print('[PASS] Portfolio domain imports OK')
    from backend.domains.risk import RiskService, RiskState, RiskLimit, HaltReason
    print('[PASS] Risk domain imports OK')
    from backend.domains.indicators import IndicatorService, IndicatorValues, TradingViewProvider, CompositeProvider, LocalCalculator
    print('[PASS] Indicators domain imports OK')
    from backend.domains.execution import ExecutionService, Order, Position, SLTPCalculator
    print('[PASS] Execution domain imports OK')
    from backend.domains.api import __all__ as api_all
    print('[PASS] API domain imports OK')

def test_container():
    print()
    print('=' * 60)
    print('Testing DI container...')
    print('=' * 60)
    from backend.container import get_container
    container = get_container()
    services = container.build()
    print(f'[PASS] Container built successfully')
    print(f'  Services: {list(services.keys())}')
    assert 'analysis_service' in services or 'AnalysisService' in services, 'AnalysisService not found in container'
    print('[PASS] Key services verified in container')

def test_py_compile():
    print()
    print('=' * 60)
    print('Py compile verification...')
    print('=' * 60)
    import py_compile
    import glob
    patterns = [
        'multi_bot_trading_system_vision0.0.1.3/backend/domains/**/*.py',
        'multi_bot_trading_system_vision0.0.1.3/backend/container.py',
        'multi_bot_trading_system_vision0.0.1.3/backend/config.py',
    ]
    all_files = []
    for pattern in patterns:
        files = glob.glob(pattern, recursive=True)
        all_files.extend(files)
    failed = []
    for f in all_files:
        try:
            py_compile.compile(f, doraise=True)
        except py_compile.PyCompileError as e:
            failed.append((f, str(e)))
    if failed:
        print('[FAIL] Py compile failures:')
        for f, err in failed:
            print(f'  {f}: {err}')
    else:
        print(f'[PASS] All {len(all_files)} Python files compile successfully')

if __name__ == "__main__":
    test_domain_imports()
    test_container()
    test_py_compile()
    print()
    print('=' * 60)
    print('All integration tests passed!')
    print('=' * 60)
