from __future__ import annotations

"""Sentiment analysis utilities using NLTK's VADER."""

from nltk.sentiment import SentimentIntensityAnalyzer
from nltk import download

# Ensure the VADER lexicon is available
try:
    _analyzer = SentimentIntensityAnalyzer()
except LookupError:  # pragma: no cover - one-time download
    download("vader_lexicon", quiet=True)
    _analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> float:
    """Return compound sentiment score (-1.0 to 1.0) for the given text."""
    if not text:
        return 0.0
    scores = _analyzer.polarity_scores(text)
    return scores["compound"]
