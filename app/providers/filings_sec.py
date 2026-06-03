import httpx
import logging
from datetime import datetime, timedelta, timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.models import FilingEvent
from app.exceptions import ProviderError

logger = logging.getLogger(__name__)

class SECProvider:
    def __init__(self, user_agent: str):
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}
        self.ticker_to_cik: dict[str, str] = {}

    def _ensure_cik_mapping(self):
        if self.ticker_to_cik:
            return

        url = "https://www.sec.gov/files/company_tickers.json"
        try:
            with httpx.Client(headers=self.headers) as client:
                response = client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                for item in data.values():
                    ticker = item["ticker"].upper()
                    cik = str(item["cik_str"]).zfill(10)
                    self.ticker_to_cik[ticker] = cik
        except Exception as e:
            logger.error(f"Failed to fetch SEC ticker mapping: {e}")
            raise ProviderError(f"SEC ticker mapping failure: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    def fetch_filings(self, symbol: str, lookback_hours: int) -> list[FilingEvent]:
        self._ensure_cik_mapping()
        cik = self.ticker_to_cik.get(symbol.upper())
        if not cik:
            logger.warning(f"CIK not found for symbol: {symbol}")
            return []

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            with httpx.Client(headers=self.headers) as client:
                response = client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"SEC API error for {symbol} (CIK {cik}): {e}")
            raise ProviderError(f"SEC API error: {e}")

        filings = []
        recent = data.get("filings", {}).get("recent", {})
        if not recent:
            return []

        lookback_limit = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        
        # SEC recent filings lists
        form_types = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])

        monitored_forms = {"8-K", "10-Q", "10-K"}

        for i in range(len(form_types)):
            form = form_types[i]
            if form not in monitored_forms:
                continue
            
            # SEC filingDate is YYYY-MM-DD. They also have acceptanceDateTime which is more precise.
            # But acceptanceDateTime is not always in 'recent'. Let's check.
            # Usually it is there as 'acceptanceDateTime'.
            acceptance_str = recent.get("acceptanceDateTime", [None])[i]
            if acceptance_str:
                # Format: 2023-10-27T16:05:01.000Z
                try:
                    filed_at = datetime.fromisoformat(acceptance_str.replace("Z", "+00:00"))
                except ValueError:
                    filed_at = datetime.strptime(filing_dates[i], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                filed_at = datetime.strptime(filing_dates[i], "%Y-%m-%d").replace(tzinfo=timezone.utc)

            if filed_at < lookback_limit:
                # Assuming they are ordered by date descending, we could break here.
                # But let's be safe for Phase 1.
                continue

            # Build URL: https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no}/{primary_doc}
            acc_no = accession_numbers[i].replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{primary_documents[i]}"

            filings.append(FilingEvent(
                symbol=symbol,
                form_type=form,
                filed_at=filed_at,
                url=url,
                description=f"SEC Form {form}"
            ))

        return filings
