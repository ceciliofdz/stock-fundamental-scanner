import sys
import logging
from app.config import get_settings
from app.services.watchlist_service import WatchlistService
from app.services.scanner_service import ScannerService
from app.services.scoring_service import ScoringService
from app.services.report_service import ReportService
from app.providers.news_provider import CompositeNewsProvider
from app.providers.earnings_finnhub import FinnhubEarningsProvider
from app.providers.filings_sec import SECProvider
from app.exceptions import ScannerError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    try:
        # 1. Load config
        settings = get_settings()
        
        # 2. Initialize Providers
        news_provider = CompositeNewsProvider(
            alpha_vantage_key=settings.alpha_vantage_api_key,
            marketaux_key=settings.marketaux_api_key
        )
        earnings_provider = FinnhubEarningsProvider(api_key=settings.finnhub_api_key)
        filings_provider = SECProvider(user_agent=settings.sec_user_agent)
        
        # 3. Initialize Services
        watchlist_service = WatchlistService(watchlist_path=settings.watchlist_path)
        scoring_service = ScoringService()
        scanner_service = ScannerService(
            news_provider=news_provider,
            earnings_provider=earnings_provider,
            filings_provider=filings_provider,
            scoring_service=scoring_service,
            lookback_hours_news=settings.lookback_hours_news,
            lookback_hours_filings=settings.lookback_hours_filings
        )
        report_service = ReportService(output_dir=settings.output_dir)

        # 4. Load Watchlist
        logger.info(f"Loading watchlist from {settings.watchlist_path}...")
        watchlist = watchlist_service.load_watchlist()
        
        # 5. Execute Scan
        results = scanner_service.scan(watchlist)
        
        # 6. Generate Reports
        if not results:
            logger.info("No results to report.")
            return

        report_service.print_console_table(results)
        csv_path = report_service.generate_csv(results)
        logger.info(f"Report saved to: {csv_path}")

    except ScannerError as e:
        logger.error(f"Scanner error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
