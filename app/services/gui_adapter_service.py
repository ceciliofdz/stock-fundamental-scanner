import pandas as pd
import yaml
from pathlib import Path
from typing import Optional
from app.config import get_settings
from app.models import WatchlistSymbol, TickerResult
from app.services.watchlist_service import WatchlistService
from app.services.scanner_service import ScannerService
from app.services.scoring_service import ScoringService
from app.providers.news_marketaux import MarketauxProvider
from app.providers.earnings_finnhub import FinnhubEarningsProvider
from app.providers.filings_sec import SECProvider
from app.exceptions import WatchlistError

class GUIAdapterService:
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize providers
        self.news_provider = MarketauxProvider(api_key=self.settings.marketaux_api_key)
        self.earnings_provider = FinnhubEarningsProvider(api_key=self.settings.finnhub_api_key)
        self.filings_provider = SECProvider(user_agent=self.settings.sec_user_agent)
        
        # Initialize services
        self.scoring_service = ScoringService()
        self.scanner_service = ScannerService(
            news_provider=self.news_provider,
            earnings_provider=self.earnings_provider,
            filings_provider=self.filings_provider,
            scoring_service=self.scoring_service,
            lookback_hours_news=self.settings.lookback_hours_news,
            lookback_hours_filings=self.settings.lookback_hours_filings
        )

    def load_symbols_from_config(self) -> list[str]:
        """Loads symbols from the default YAML config file."""
        if not self.settings.watchlist_path.exists():
            return []
        
        try:
            with open(self.settings.watchlist_path, "r") as f:
                data = yaml.safe_load(f)
                symbols_data = data.get("symbols", [])
                
                symbols = []
                for item in symbols_data:
                    if isinstance(item, str):
                        symbols.append(item.upper())
                    elif isinstance(item, dict):
                        if item.get("enabled", True):
                            symbols.append(item.get("symbol", "").upper())
                return sorted(list(set(filter(None, symbols))))
        except Exception:
            return []

    def save_symbols_to_config(self, symbols: list[str]):
        """Saves a simple list of symbols to the YAML config file."""
        data = {"symbols": sorted([s.upper().strip() for s in symbols if s.strip()])}
        self.settings.watchlist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings.watchlist_path, "w") as f:
            yaml.safe_dump(data, f)

    def run_scan_for_symbols(self, symbols: list[str]) -> pd.DataFrame:
        """Runs the scan for a given list of symbols and returns a DataFrame."""
        if not symbols:
            return pd.DataFrame()
            
        watchlist = [WatchlistSymbol(symbol=s.upper().strip()) for s in symbols if s.strip()]
        results = self.scanner_service.scan(watchlist)
        
        return self._results_to_df(results)

    def _results_to_df(self, results: list[TickerResult]) -> pd.DataFrame:
        data = []
        for r in results:
            data.append({
                "symbol": r.symbol,
                "score": r.score,
                "news_count": r.news_count,
                "avg_sentiment": round(r.avg_sentiment, 2) if r.avg_sentiment is not None else None,
                "earnings": "Today" if r.has_earnings_today else ("Tomorrow" if r.has_earnings_tomorrow else "No"),
                "latest_filing": r.latest_filing_type or "None",
                "latest_filing_at": r.latest_filing_at.strftime("%Y-%m-%d %H:%M") if r.latest_filing_at else "",
                "score_reasons": "; ".join(r.score_reasons)
            })
        return pd.DataFrame(data)

    def normalize_symbols(self, raw_input: str) -> list[str]:
        """Normalizes comma or newline separated strings into a clean list of tickers."""
        if not raw_input:
            return []
        
        # Split by comma or newline
        import re
        parts = re.split(r'[,\n]', raw_input)
        
        normalized = []
        for p in parts:
            clean = p.strip().upper()
            if clean and clean not in normalized:
                normalized.append(clean)
        return normalized
