import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, date
from app.services.scanner_service import ScannerService
from app.models import WatchlistSymbol, NewsArticle, EarningsEvent, FilingEvent

def test_scanner_orchestration():
    # Mocks
    news_mock = MagicMock()
    news_mock.fetch_news.return_value = [
        NewsArticle(symbol="AAPL", title="News 1", published_at=datetime.now(timezone.utc), source="S1", url="U1", sentiment_score=0.5)
    ]
    
    earnings_mock = MagicMock()
    earnings_mock.fetch_earnings.return_value = [
        EarningsEvent(symbol="AAPL", event_date=date.today(), time_of_day="AMC")
    ]
    
    filings_mock = MagicMock()
    filings_mock.fetch_filings.return_value = []
    
    scoring_mock = MagicMock()
    scoring_mock.calculate_score.return_value = (50, ["reason 1"])
    
    service = ScannerService(
        news_provider=news_mock,
        earnings_provider=earnings_mock,
        filings_provider=filings_mock,
        scoring_service=scoring_mock,
        lookback_hours_news=36,
        lookback_hours_filings=48
    )
    
    watchlist = [WatchlistSymbol(symbol="AAPL")]
    results = service.scan(watchlist)
    
    assert len(results) == 1
    assert results[0].symbol == "AAPL"
    assert results[0].score == 50
    assert results[0].news_count == 1
    assert results[0].has_earnings_today is True
    
    news_mock.fetch_news.assert_called_once_with("AAPL", 36)
    earnings_mock.fetch_earnings.assert_called_once_with(["AAPL"])
    filings_mock.fetch_filings.assert_called_once_with("AAPL", 48)
