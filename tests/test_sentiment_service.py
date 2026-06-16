from datetime import datetime, timezone, timedelta

import pytest

from app.models import NewsArticle
from app.services.sentiment_service import SentimentService


def _article(symbol: str, score: float, hours_ago: float) -> NewsArticle:
    return NewsArticle(
        symbol=symbol,
        title="Headline",
        published_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        source="Test",
        url="https://example.com",
        sentiment_score=score,
    )


def test_sentiment_empty_news():
    summary = SentimentService().analyze([])
    assert summary.avg_sentiment is None
    assert summary.label is None
    assert summary.confidence == 0.0


def test_sentiment_classification():
    now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    news = [
        _article("AAPL", 0.5, 2),
        _article("AAPL", 0.4, 4),
        _article("AAPL", 0.3, 6),
    ]
    summary = SentimentService().analyze(news, now=now)
    assert summary.label == "very_positive"
    assert summary.positive_count == 3
    assert summary.weighted_sentiment is not None
    assert summary.weighted_sentiment > summary.avg_sentiment * 0.9


def test_sentiment_recent_news_weighs_more():
    now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    news = [
        _article("AAPL", 0.8, 1),
        _article("AAPL", -0.2, 30),
        _article("AAPL", -0.2, 32),
    ]
    summary = SentimentService().analyze(news, now=now)
    assert summary.weighted_sentiment > summary.avg_sentiment


def test_sentiment_trend_improving():
    now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    news = [
        _article("AAPL", 0.6, 1),
        _article("AAPL", 0.5, 2),
        _article("AAPL", -0.1, 20),
        _article("AAPL", -0.2, 22),
    ]
    summary = SentimentService().analyze(news, now=now)
    assert summary.trend == "improving"


def test_sentiment_relevance_weighs_more():
    now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    # Two articles at same time, one more relevant than other
    news = [
        NewsArticle(
            symbol="AAPL",
            title="Relevant",
            published_at=now - timedelta(hours=1),
            source="Test",
            url="url",
            sentiment_score=0.8,
            relevance_score=1.0
        ),
        NewsArticle(
            symbol="AAPL",
            title="Irrelevant",
            published_at=now - timedelta(hours=1),
            source="Test",
            url="url",
            sentiment_score=-0.2,
            relevance_score=0.1
        ),
    ]
    summary = SentimentService().analyze(news, now=now)
    # The 0.8 should dominate
    assert summary.weighted_sentiment > 0.6


def test_sentiment_negative_label():
    now = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    news = [
        _article("AAPL", -0.5, 1),
        _article("AAPL", -0.4, 2),
    ]
    summary = SentimentService().analyze(news, now=now)
    assert summary.label == "very_negative"
    assert summary.negative_count == 2
