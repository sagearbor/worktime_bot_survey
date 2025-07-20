"""Basic NLP processing utilities for the chatbot."""

from __future__ import annotations

import re
from typing import Dict, Tuple, List

from textblob import TextBlob

from ..app import load_config
from pathlib import Path


def extract_time_allocations(text: str, config_path: Path) -> Dict[str, float]:
    """Parse natural language text into activity percentage mapping."""
    config = load_config(config_path)
    categories = {a["category"].lower(): a["category"] for a in config.get("activities", [])}

    allocation: Dict[str, float] = {}
    # regex like "60% meetings" or "30% research"
    pattern = re.compile(r"(\d+(?:\.\d+)?)%\s*(\w+)", re.IGNORECASE)
    for percent, activity in pattern.findall(text):
        act_key = activity.lower()
        if act_key in categories:
            allocation[categories[act_key]] = float(percent)
    return allocation


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """Return top keywords from text using simple noun extraction."""
    blob = TextBlob(text)
    nouns = [word.lemmatize().lower() for word, tag in blob.tags if tag.startswith("NN")]
    freq: Dict[str, int] = {}
    for n in nouns:
        freq[n] = freq.get(n, 0) + 1
    return sorted(freq, key=freq.get, reverse=True)[:top_n]


def sentiment_score(text: str) -> float:
    """Return sentiment polarity score from -1 to 1."""
    blob = TextBlob(text)
    return float(blob.sentiment.polarity)
