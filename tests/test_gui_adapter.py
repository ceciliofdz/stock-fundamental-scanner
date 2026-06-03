import pytest
import pandas as pd
from unittest.mock import MagicMock
from app.services.gui_adapter_service import GUIAdapterService
from app.models import TickerResult

def test_normalize_symbols():
    adapter = GUIAdapterService()
    raw = "aapl, nvda\nAMD, tsla,,  "
    normalized = adapter.normalize_symbols(raw)
    assert normalized == ["AAPL", "NVDA", "AMD", "TSLA"]

def test_results_to_df():
    adapter = GUIAdapterService()
    results = [
        TickerResult(
            symbol="AAPL",
            score=80,
            news_count=5,
            avg_sentiment=0.45,
            has_earnings_today=True,
            score_reasons=["reason 1", "reason 2"]
        )
    ]
    df = adapter._results_to_df(results)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["symbol"] == "AAPL"
    assert df.iloc[0]["score"] == 80
    assert df.iloc[0]["earnings"] == "Today"
    assert df.iloc[0]["score_reasons"] == "reason 1; reason 2"
