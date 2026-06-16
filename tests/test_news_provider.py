from app.providers.news_provider import MarketauxProvider, AlphaVantageProvider


def test_marketaux_extract_symbol_info():
    entities = [
        {"symbol": "aapl", "sentiment_score": 0.2, "match_score": 0.8},
        {"symbol": "MSFT", "sentiment_score": 0.9, "match_score": 0.9},
    ]
    info = MarketauxProvider._extract_symbol_info(entities, "AAPL")
    assert info["score"] == 0.2
    assert info["relevance"] == 0.8


def test_marketaux_extract_symbol_info_prefers_best_match():
    entities = [
        {"symbol": "NVDA", "sentiment_score": 0.1, "match_score": 0.4},
        {"symbol": "NVDA", "sentiment_score": 0.6, "match_score": 0.95},
    ]
    info = MarketauxProvider._extract_symbol_info(entities, "NVDA")
    assert info["score"] == 0.6
    assert info["relevance"] == 0.95


def test_alphavantage_extract_symbol_info():
    ticker_sentiment = [
        {"ticker": "AAPL", "ticker_sentiment_score": "0.45", "relevance_score": "0.85"},
        {"ticker": "MSFT", "ticker_sentiment_score": "0.15", "relevance_score": "0.5"},
    ]
    info = AlphaVantageProvider._extract_symbol_info(ticker_sentiment, "AAPL")
    assert info["score"] == 0.45
    assert info["relevance"] == 0.85


def test_extract_symbol_info_missing():
    info = MarketauxProvider._extract_symbol_info([], "AAPL")
    assert info["score"] is None
    assert info["relevance"] == 1.0
