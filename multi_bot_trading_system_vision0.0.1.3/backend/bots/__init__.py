# filepath: bots/__init__.py
"""Bots module for trading bots"""

from .base_bot import BaseBot, Signal
from .sr_bot import SRBot
from .smc_bot import SMCBot
from .harmonic_bot import HarmonicBot
from .trend_bot import TrendBot

__all__ = ['BaseBot', 'Signal', 'SRBot', 'SMCBot', 'HarmonicBot', 'TrendBot']