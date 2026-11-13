from backend.analyzers.base_analyzer import AnalysisResult, BaseAnalyzer
from backend.analyzers.engine import AnalysisEngine
from backend.analyzers.registry import AnalyzerRegistry


class ModeAnalyzer(BaseAnalyzer):
    def __init__(self, analyzer_id: str) -> None:
        self.analyzer_id = analyzer_id

    def get_metadata(self):
        return {
            "id": self.analyzer_id,
            "name": self.analyzer_id,
            "category": "indicator",
            "description": "",
            "icon": "",
            "config_fields": [],
        }

    def get_default_config(self):
        return {}

    def validate_config(self, config):
        return []

    def analyze(self, context, config):
        return AnalysisResult(
            analyzer_id=self.analyzer_id,
            symbol=context.symbol,
            timeframe=context.timeframe,
            mode=context.mode,
        )


def test_analyzers_receive_their_own_current_or_history_mode():
    registry = AnalyzerRegistry()
    registry.register(ModeAnalyzer("test.current"))
    registry.register(ModeAnalyzer("test.history"))
    engine = AnalysisEngine(registry)

    response = engine.run_analysis(
        symbol="BTCUSDT",
        timeframe="1h",
        mode="current",
        selected=[
            {"analyzer_id": "test.current", "mode": "current", "config": {}},
            {"analyzer_id": "test.history", "mode": "history", "config": {}},
        ],
        all_candles=[],
    )

    assert response["results"]["test.current"]["mode"] == "current"
    assert response["results"]["test.history"]["mode"] == "history"
