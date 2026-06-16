from datetime import datetime, date
from pydantic import BaseModel, Field

class WatchlistSymbol(BaseModel):
    symbol: str
    enabled: bool = True

class NewsArticle(BaseModel):
    symbol: str
    title: str
    published_at: datetime
    source: str
    url: str
    sentiment_score: float | None = None
    relevance_score: float = 1.0
    summary: str | None = None

class EarningsEvent(BaseModel):
    symbol: str
    event_date: date
    time_of_day: str | None = None

class FilingEvent(BaseModel):
    symbol: str
    form_type: str
    filed_at: datetime
    url: str | None = None
    description: str | None = None

class TickerResult(BaseModel):
    symbol: str
    news: list[NewsArticle] = Field(default_factory=list)
    earnings: list[EarningsEvent] = Field(default_factory=list)
    filings: list[FilingEvent] = Field(default_factory=list)
    
    # Derived fields
    news_count: int = 0
    avg_sentiment: float | None = None
    weighted_sentiment: float | None = None
    sentiment_label: str | None = None
    sentiment_trend: str | None = None
    sentiment_confidence: float | None = None
    positive_news_count: int = 0
    negative_news_count: int = 0
    neutral_news_count: int = 0
    has_earnings_today: bool = False
    has_earnings_tomorrow: bool = False
    latest_filing_type: str | None = None
    latest_filing_at: datetime | None = None
    
    score: int = 0
    score_reasons: list[str] = Field(default_factory=list)
