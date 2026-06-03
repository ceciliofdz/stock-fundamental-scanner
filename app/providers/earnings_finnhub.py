import httpx
import logging
from datetime import date, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.models import EarningsEvent
from app.exceptions import ProviderError

logger = logging.getLogger(__name__)

class FinnhubEarningsProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1/calendar/earnings"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    def fetch_earnings(self, symbols: list[str]) -> list[EarningsEvent]:
        # Finnhub earnings calendar
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        params = {
            "from": today.isoformat(),
            "to": tomorrow.isoformat()
        }
        headers = {
            "X-Finnhub-Token": self.api_key
        }

        try:
            with httpx.Client() as client:
                response = client.get(self.base_url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"Finnhub API error: {e}")
            raise ProviderError(f"Finnhub API error: {e}")

        events = []
        symbol_set = set(symbols)
        
        # Finnhub returns { "earningsCalendar": [...] }
        earnings_list = data.get("earningsCalendar", [])
        
        for item in earnings_list:
            symbol = item.get("symbol")
            if symbol in symbol_set:
                event_date_str = item.get("date")
                if not event_date_str:
                    continue
                
                try:
                    event_date = date.fromisoformat(event_date_str)
                except ValueError:
                    continue
                
                # Finnhub time field: "amc", "bmo", or similar
                events.append(EarningsEvent(
                    symbol=symbol,
                    event_date=event_date,
                    time_of_day=item.get("hour")
                ))
        
        return events
