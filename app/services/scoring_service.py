from datetime import datetime, timedelta, timezone
from app.models import TickerResult

class ScoringService:
    def calculate_score(self, result: TickerResult, lookback_hours_filings: int) -> tuple[int, list[str]]:
        score = 0
        reasons = []

        # Earnings rules
        if result.has_earnings_today:
            score += 30
            reasons.append("earnings today")
        elif result.has_earnings_tomorrow:
            score += 20
            reasons.append("earnings tomorrow")

        # Filings rules
        now = datetime.now(timezone.utc)
        if result.latest_filing_at:
            # We need to be careful with timezones. result.latest_filing_at should be UTC.
            filing_age = now - result.latest_filing_at
            
            if result.latest_filing_type == "8-K" and filing_age <= timedelta(hours=12):
                score += 25
                reasons.append("recent 8-K filing (last 12h)")
            elif result.latest_filing_type in ["10-Q", "10-K"] and filing_age <= timedelta(hours=24):
                score += 15
                reasons.append(f"recent {result.latest_filing_type} filing (last 24h)")
            elif filing_age <= timedelta(hours=lookback_hours_filings):
                score += 10
                reasons.append(f"monitored filing in lookback ({result.latest_filing_type})")

        # News count rules
        if result.news_count >= 5:
            score += 10
            reasons.append(f"{result.news_count} news articles in lookback")
        elif result.news_count >= 3:
            score += 5
            reasons.append(f"{result.news_count} news articles in lookback")

        # Sentiment rules
        if result.avg_sentiment is not None:
            abs_sent = abs(result.avg_sentiment)
            sentiment_type = "positive" if result.avg_sentiment > 0 else "negative"
            if abs_sent >= 0.35:
                score += 10
                reasons.append(f"strongly {sentiment_type} news sentiment ({result.avg_sentiment:.2f})")
            elif abs_sent >= 0.20:
                score += 5
                reasons.append(f"moderate {sentiment_type} news sentiment ({result.avg_sentiment:.2f})")

        # Clamp score
        final_score = max(0, min(100, score))
        return final_score, reasons
