import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from app.providers.earnings_finnhub import FinnhubEarningsProvider
from app.models import EarningsEvent

def test_fetch_earnings_success():
    provider = FinnhubEarningsProvider(api_key="test_key")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "earningsCalendar": [
            {
                "symbol": "AAPL",
                "date": "2023-10-27",
                "hour": "amc"
            },
            {
                "symbol": "TSLA",
                "date": "2023-10-28",
                "hour": "bmo"
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.get", return_value=mock_response) as mock_get:
        events = provider.fetch_earnings(["AAPL"])
        
        # Verify headers
        args, kwargs = mock_get.call_args
        assert kwargs["headers"]["X-Finnhub-Token"] == "test_key"
        
        assert len(events) == 1
        assert events[0].symbol == "AAPL"
        assert events[0].event_date == date(2023, 10, 27)
        assert events[0].time_of_day == "amc"

def test_fetch_earnings_empty():
    provider = FinnhubEarningsProvider(api_key="test_key")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"earningsCalendar": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.get", return_value=mock_response):
        events = provider.fetch_earnings(["AAPL"])
        assert len(events) == 0
