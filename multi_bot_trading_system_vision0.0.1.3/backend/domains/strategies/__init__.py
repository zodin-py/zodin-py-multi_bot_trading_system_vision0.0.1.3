"""Strategies domain — SR, SMC, Harmonic, Trend pattern bots.

Each bot analyses market structure (support/resistance, order blocks,
harmonic patterns, MA alignment) and emits weighted buy/sell/hold signals.
"""

from backend.domains.strategies.base import StrategyBot, Signal, SignalType
from backend.domains.strategies.sr_bot import SRBot
from backend.domains.strategies.smc_bot import SMCBot
from backend.domains.strategies.harmonic_bot import HarmonicBot
from backend.domains.strategies.trend_bot import TrendBot
from backend.domains.strategies.service import StrategiesService

__all__ = [
    'StrategyBot',
    'Signal',
    'SignalType',
    'SRBot',
    'SMCBot',
    'HarmonicBot',
    'TrendBot',
    'StrategiesService',
]
