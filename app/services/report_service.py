import pandas as pd
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
from app.models import TickerResult

class ReportService:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_csv(self, results: list[TickerResult]) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"scan_{timestamp}.csv"
        file_path = self.output_dir / filename

        data = []
        for r in results:
            data.append({
                "symbol": r.symbol,
                "score": r.score,
                "news_count": r.news_count,
                "avg_sentiment": f"{r.avg_sentiment:.2f}" if r.avg_sentiment is not None else "",
                "weighted_sentiment": f"{r.weighted_sentiment:.2f}" if r.weighted_sentiment is not None else "",
                "sentiment_label": r.sentiment_label or "",
                "sentiment_trend": r.sentiment_trend or "",
                "sentiment_confidence": r.sentiment_confidence if r.sentiment_confidence is not None else "",
                "positive_news": r.positive_news_count,
                "negative_news": r.negative_news_count,
                "has_earnings_today": r.has_earnings_today,
                "has_earnings_tomorrow": r.has_earnings_tomorrow,
                "latest_filing_type": r.latest_filing_type or "none",
                "latest_filing_at": r.latest_filing_at.isoformat() if r.latest_filing_at else "",
                "score_reasons": "; ".join(r.score_reasons)
            })

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        return file_path

    def print_console_table(self, results: list[TickerResult]):
        table_data = []
        for i, r in enumerate(results, 1):
            earnings_str = "today" if r.has_earnings_today else ("tomorrow" if r.has_earnings_tomorrow else "no")
            filing_str = r.latest_filing_type or "none"
            
            table_data.append([
                i,
                r.symbol,
                r.score,
                r.news_count,
                earnings_str,
                filing_str,
                "; ".join(r.score_reasons)
            ])

        headers = ["Rank", "Symbol", "Score", "News", "Earnings", "Filing", "Reasons"]
        print("\n" + tabulate(table_data, headers=headers, tablefmt="grid") + "\n")
