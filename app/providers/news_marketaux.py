import httpx
import logging
from datetime import datetime, timedelta, timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.models import NewsArticle
from app.exceptions import ProviderError

logger = logging.getLogger(__name__)

class MarketauxProvider:
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
        except httpx.HTTPStatusError as e:
            logger.error(f"Marketaux API error for {symbol}: {e.response.status_code} - {e.response.text}")
            raise ProviderError(f"Marketaux API error: {e}")
        except httpx.RequestError as e:
            logger.warning(f"Marketaux request error for {symbol}: {e!r}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching news for {symbol}: {e}")
            raise ProviderError(f"Marketaux unexpected error: {e}")

        articles = []
        for item in data.get("data", []):
            # Marketaux provides entities, we can check if our symbol is there and get its sentiment
            sentiment = None
            for entity in item.get("entities", []):
                if entity.get("symbol") == symbol:
                    sentiment = entity.get("sentiment_score")
                    break
            
            # published_at: "2023-10-27T12:00:00.000000Z"
            pub_at_str = item.get("published_at")
            try:
                # Remove Z and use fromisoformat if possible, or just parse
                pub_at = datetime.fromisoformat(pub_at_str.replace("Z", "+00:00"))
            except ValueError:
                pub_at = datetime.now(timezone.utc)

            articles.append(NewsArticle(
                symbol=symbol,
                title=item.get("title", ""),
                published_at=pub_at,
                source=item.get("source", ""),
                url=item.get("url", ""),
                sentiment_score=sentiment,
                summary=item.get("description")
            ))
        
        return articles
