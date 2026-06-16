from dataclasses import dataclass
from datetime import datetime, timezone

from app.models import NewsArticle

# Marketaux sentiment scores range from -1 (negative) to +1 (positive).
STRONG_THRESHOLD = 0.35
MODERATE_THRESHOLD = 0.15
NEUTRAL_BAND = 0.15
TREND_DELTA_THRESHOLD = 0.08
SENTIMENT_HALF_LIFE_HOURS = 12.0


@dataclass(frozen=True)
class SentimentSummary:
    avg_sentiment: float | None
    weighted_sentiment: float | None
    label: str | None
    trend: str | None
    confidence: float
    positive_count: int
    negative_count: int
    neutral_count: int
    articles_with_sentiment: int


class SentimentService:
    def analyze(self, news: list[NewsArticle], *, now: datetime | None = None) -> SentimentSummary:
        reference = now or datetime.now(timezone.utc)
        scored = [article for article in news if article.sentiment_score is not None]

        if not scored:
            return SentimentSummary(
                avg_sentiment=None,
                weighted_sentiment=None,
                label=None,
                trend=None,
                confidence=0.0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                articles_with_sentiment=0,
            )

        positive_count = sum(1 for a in scored if a.sentiment_score > NEUTRAL_BAND)
        negative_count = sum(1 for a in scored if a.sentiment_score < -NEUTRAL_BAND)
        neutral_count = len(scored) - positive_count - negative_count

        simple_avg = sum(a.sentiment_score for a in scored) / len(scored)
        weighted_avg = self._weighted_average(scored, reference)
        confidence = len(scored) / len(news) if news else 0.0
        label = self._classify(weighted_avg)
        trend = self._detect_trend(scored, reference)

        return SentimentSummary(
            avg_sentiment=simple_avg,
            weighted_sentiment=weighted_avg,
            label=label,
            trend=trend,
            confidence=round(confidence, 2),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            articles_with_sentiment=len(scored),
        )

    def _weight_for_age(self, age_hours: float) -> float:
        return 0.5 ** (age_hours / SENTIMENT_HALF_LIFE_HOURS)

    def _weighted_average(self, articles: list[NewsArticle], now: datetime) -> float:
        total_weight = 0.0
        weighted_sum = 0.0

        for article in articles:
            published = article.published_at
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            age_hours = max(0.0, (now - published).total_seconds() / 3600)
            
            # Combine time weight and relevance weight
            time_weight = self._weight_for_age(age_hours)
            relevance_weight = article.relevance_score
            combined_weight = time_weight * relevance_weight
            
            weighted_sum += article.sentiment_score * combined_weight
            total_weight += combined_weight

        return weighted_sum / total_weight if total_weight else 0.0

    def _classify(self, score: float) -> str:
        if score >= STRONG_THRESHOLD:
            return "very_positive"
        if score >= MODERATE_THRESHOLD:
            return "positive"
        if score <= -STRONG_THRESHOLD:
            return "very_negative"
        if score <= -MODERATE_THRESHOLD:
            return "negative"
        return "neutral"

    def _detect_trend(self, articles: list[NewsArticle], now: datetime) -> str | None:
        if len(articles) < 4:
            return None

        sorted_articles = sorted(
            articles,
            key=lambda a: a.published_at if a.published_at.tzinfo else a.published_at.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        midpoint = len(sorted_articles) // 2
        recent = sorted_articles[:midpoint]
        older = sorted_articles[midpoint:]

        recent_avg = self._weighted_average(recent, now)
        older_avg = self._weighted_average(older, now)
        delta = recent_avg - older_avg

        if delta >= TREND_DELTA_THRESHOLD:
            return "improving"
        if delta <= -TREND_DELTA_THRESHOLD:
            return "declining"
        return "stable"
