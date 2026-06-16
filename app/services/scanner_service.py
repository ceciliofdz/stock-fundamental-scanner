import logging
from datetime import datetime, timezone
from app.models import WatchlistSymbol, TickerResult, NewsArticle, EarningsEvent, FilingEvent
from app.providers.news_provider import CompositeNewsProvider
from app.providers.earnings_finnhub import FinnhubEarningsProvider
from app.providers.filings_sec import SECProvider
from app.services.scoring_service import ScoringService
from app.services.sentiment_service import SentimentService
from app.utils.time_utils import is_today, is_tomorrow

logger = logging.getLogger(__name__)

class ScannerService:
    def __init__(
        self,
        news_provider: CompositeNewsProvider,
        earnings_provider: FinnhubEarningsProvider,
        filings_provider: SECProvider,
        scoring_service: ScoringService,
        lookback_hours_news: int,
        lookback_hours_filings: int,
        sentiment_service: SentimentService | None = None,
    ):
        self.news_provider = news_provider
        self.earnings_provider = earnings_provider
        self.filings_provider = filings_provider
        self.scoring_service = scoring_service
        self.sentiment_service = sentiment_service or SentimentService()
        self.lookback_hours_news = lookback_hours_news
        self.lookback_hours_filings = lookback_hours_filings

    def scan(self, watchlist: list[WatchlistSymbol]) -> list[TickerResult]:
        symbols = [ws.symbol for ws in watchlist]
        logger.info(f"Starting scan for {len(symbols)} symbols...")

        # 1. Fetch batch data where possible (Earnings)
        all_earnings = []
        try:
            all_earnings = self.earnings_provider.fetch_earnings(symbols)
        except Exception as e:
            logger.warning(f"Failed to fetch earnings: {e}")

        # Map earnings to symbols
        earnings_map: dict[str, list[EarningsEvent]] = {s: [] for s in symbols}
        for e in all_earnings:
            if e.symbol in earnings_map:
                earnings_map[e.symbol].append(e)

        results = []

        # 2. Loop through symbols for News and Filings (per-ticker usually)
        for ws in watchlist:
            symbol = ws.symbol
            logger.info(f"Processing {symbol}...")
            
            # Fetch news
            news = []
            try:
                news = self.news_provider.fetch_news(symbol, self.lookback_hours_news)
            except Exception as e:
                logger.warning(f"Failed to fetch news for {symbol}: {e}")

            # Fetch filings
            filings = []
            try:
                filings = self.filings_provider.fetch_filings(symbol, self.lookback_hours_filings)
            except Exception as e:
                logger.warning(f"Failed to fetch filings for {symbol}: {e}")

            # 3. Compute derived fields
            news_count = len(news)
            sentiment = self.sentiment_service.analyze(news)
            
            ticker_earnings = earnings_map.get(symbol, [])
            has_earnings_today = any(is_today(e.event_date) for e in ticker_earnings)
            has_earnings_tomorrow = any(is_tomorrow(e.event_date) for e in ticker_earnings)
            
            latest_filing = None
            if filings:
                # Sort by date descending just in case
                filings.sort(key=lambda x: x.filed_at, reverse=True)
                latest_filing = filings[0]

            result = TickerResult(
                symbol=symbol,
                news=news,
                earnings=ticker_earnings,
                filings=filings,
                news_count=news_count,
                avg_sentiment=sentiment.avg_sentiment,
                weighted_sentiment=sentiment.weighted_sentiment,
                sentiment_label=sentiment.label,
                sentiment_trend=sentiment.trend,
                sentiment_confidence=sentiment.confidence,
                positive_news_count=sentiment.positive_count,
                negative_news_count=sentiment.negative_count,
                neutral_news_count=sentiment.neutral_count,
                has_earnings_today=has_earnings_today,
                has_earnings_tomorrow=has_earnings_tomorrow,
                latest_filing_type=latest_filing.form_type if latest_filing else None,
                latest_filing_at=latest_filing.filed_at if latest_filing else None
            )

            # 4. Score
            score, reasons = self.scoring_service.calculate_score(result, self.lookback_hours_filings)
            result.score = score
            result.score_reasons = reasons

            results.append(result)

        # 5. Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        logger.info("Scan completed.")
        return results
