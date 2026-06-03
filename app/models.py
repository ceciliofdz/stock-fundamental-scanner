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
    has_earnings_today: bool = False
    has_earnings_tomorrow: bool = False
    latest_filing_type: str | None = None
    latest_filing_at: datetime | None = None
    
    score: int = 0
    score_reasons: list[str] = Field(default_factory=list)
