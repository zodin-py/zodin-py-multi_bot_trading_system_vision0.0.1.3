"""Analysis domain package.

Provides market analysis and decision-making capabilities (the 'brain').
"""

from backend.domains.analysis.models import AggregatedSignal, BotSignal, SignalType
from backend.domains.analysis.brain import Brain
from backend.domains.analysis.service import AnalysisService

__all__ = [
    'AggregatedSignal',
    'BotSignal',
    'SignalType',
    'Brain',
    'AnalysisService',
]
