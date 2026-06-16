import httpx
import logging
from datetime import datetime, timedelta, timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.models import NewsArticle
from app.exceptions import ProviderError

logger = logging.getLogger(__name__)

class AlphaVantageProvider:
    """Alpha Vantage news provider."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    def fetch_news(self, symbol: str, lookback_hours: int) -> list[NewsArticle]:
        """Fetch news from Alpha Vantage NEWS_SENTIMENT endpoint."""
        if not self.api_key:
            return []
            
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol.upper(),
            "apikey": self.api_key,
            "limit": 100
        }

        try:
            with httpx.Client() as client:
                response = client.get(self.base_url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {e.response.status_code}")
            raise ProviderError(f"Alpha Vantage API error: {e}")
        except httpx.RequestError as e:
            logger.warning(f"Alpha Vantage request error for {symbol}: {e!r}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching news from Alpha Vantage for {symbol}: {e}")
            raise ProviderError(f"Alpha Vantage unexpected error: {e}")

        # Check for error message in response
        if "Error Message" in data or "Note" in data:
            logger.warning(f"Alpha Vantage API issue: {data.get('Error Message') or data.get('Note')}")
            # If we hit rate limits (Note), we should probably raise an error to trigger fallback
            if "Note" in data and "rate limit" in data.get("Note", "").lower():
                raise ProviderError(f"Alpha Vantage rate limit: {data.get('Note')}")
            return []

        symbol_upper = symbol.upper()
        articles = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        
        for item in data.get("feed", []):
            # Filter by time
            pub_at_str = item.get("time_published")
            try:
                # Format: "20231027T120000"
                pub_at = datetime.strptime(pub_at_str, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
                if pub_at < cutoff_time:
                    continue
            except (ValueError, TypeError):
                pub_at = datetime.now(timezone.utc)

            # Extract sentiment and relevance for this symbol
            sentiment_data = self._extract_symbol_info(item.get("ticker_sentiment", []), symbol_upper)
            
            articles.append(NewsArticle(
                symbol=symbol,
                title=item.get("title", ""),
                published_at=pub_at,
                source=item.get("source", ""),
                url=item.get("url", ""),
                sentiment_score=sentiment_data["score"],
                relevance_score=sentiment_data["relevance"],
                summary=item.get("summary")
            ))
        
        return articles

    @staticmethod
    def _extract_symbol_info(ticker_sentiments: list[dict], symbol: str) -> dict:
        """Extract sentiment score and relevance for the given symbol."""
        for ticker_info in ticker_sentiments:
            if str(ticker_info.get("ticker", "")).upper() == symbol:
                try:
                    score = float(ticker_info.get("ticker_sentiment_score", 0.0))
                    relevance = float(ticker_info.get("relevance_score", 1.0))
                    return {"score": score, "relevance": relevance}
                except (ValueError, TypeError):
                    pass
        return {"score": None, "relevance": 1.0}


class MarketauxProvider:
    """Marketaux news provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.marketaux.com/v1/news/all"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    def fetch_news(self, symbol: str, lookback_hours: int) -> list[NewsArticle]:
        if not self.api_key:
            return []
            
        published_after = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).strftime("%Y-%m-%dT%H:%M")
        
        params = {
            "symbols": symbol,
            "filter_entities": "true",
            "published_after": published_after,
            "api_token": self.api_key,
            "language": "en"
        }

        try:
            with httpx.Client() as client:
                response = client.get(self.base_url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Marketaux API error for {symbol}: {e}")
            raise ProviderError(f"Marketaux API error: {e}")

        symbol_upper = symbol.upper()
        articles = []
        for item in data.get("data", []):
            info = self._extract_symbol_info(item.get("entities", []), symbol_upper)
            
            # published_at: "2023-10-27T12:00:00.000000Z"
            pub_at_str = item.get("published_at")
            try:
                pub_at = datetime.fromisoformat(pub_at_str.replace("Z", "+00:00"))
            except ValueError:
                pub_at = datetime.now(timezone.utc)

            articles.append(NewsArticle(
                symbol=symbol,
                title=item.get("title", ""),
                published_at=pub_at,
                source=item.get("source", ""),
                url=item.get("url", ""),
                sentiment_score=info["score"],
                relevance_score=info["relevance"],
                summary=item.get("description")
            ))
        
        return articles

    @staticmethod
    def _extract_symbol_info(entities: list[dict], symbol: str) -> dict:
        """Pick the best-matching entity for the requested ticker."""
        matches = [
            entity for entity in entities
            if str(entity.get("symbol", "")).upper() == symbol
        ]
        if not matches:
            return {"score": None, "relevance": 1.0}

        def match_rank(entity: dict) -> tuple[float, float]:
            match_score = entity.get("match_score")
            sentiment = entity.get("sentiment_score")
            return (
                float(match_score) if match_score is not None else 0.0,
                abs(float(sentiment)) if sentiment is not None else 0.0,
            )

        best = max(matches, key=match_rank)
        return {
            "score": best.get("sentiment_score"),
            "relevance": float(best.get("match_score", 1.0))
        }


class CompositeNewsProvider:
    """Orchestrator that tries Alpha Vantage first, then falls back to Marketaux."""

    def __init__(self, alpha_vantage_key: str, marketaux_key: str):
        self.alpha_vantage = AlphaVantageProvider(alpha_vantage_key)
        self.marketaux = MarketauxProvider(marketaux_key)

    def fetch_news(self, symbol: str, lookback_hours: int) -> list[NewsArticle]:
        # Try Alpha Vantage first
        try:
            logger.info(f"Trying Alpha Vantage for {symbol}...")
            articles = self.alpha_vantage.fetch_news(symbol, lookback_hours)
            if articles:
                logger.info(f"Alpha Vantage returned {len(articles)} articles for {symbol}.")
                return articles
            logger.info(f"Alpha Vantage returned no articles for {symbol}. Falling back to Marketaux...")
        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {symbol}: {e}. Falling back to Marketaux...")

        # Fallback to Marketaux
        try:
            logger.info(f"Trying Marketaux for {symbol}...")
            return self.marketaux.fetch_news(symbol, lookback_hours)
        except Exception as e:
            logger.error(f"Marketaux also failed for {symbol}: {e}")
            # Instead of raising ProviderError, return empty list to allow the scan to continue
            return []
