"""Problem aggregation engine for chatbot feedback."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import ChatbotFeedback, ProblemIdentification
from ..chatbot.nlp_processor import extract_keywords, sentiment_score


class ProblemAggregator:
    """Aggregate chatbot problem reports into ProblemIdentification records."""

    def __init__(self, session: Session):
        self.session = session

    def process_unprocessed_feedback(self) -> None:
        """Cluster unprocessed problem reports and update frequency counts."""
        feedback_items: List[ChatbotFeedback] = (
            self.session.query(ChatbotFeedback)
            .filter(ChatbotFeedback.processed == False)
            .filter(ChatbotFeedback.message_type == "problem_report")
            .all()
        )
        for fb in feedback_items:
            desc = fb.message_text.strip()
            existing = (
                self.session.query(ProblemIdentification)
                .filter(func.lower(ProblemIdentification.description) == desc.lower())
                .first()
            )
            if existing:
                existing.frequency_count += 1
                existing.last_reported = fb.timestamp
            else:
                existing = ProblemIdentification(
                    description=desc,
                    frequency_count=1,
                    first_reported=fb.timestamp,
                    last_reported=fb.timestamp,
                )
                self.session.add(existing)
            fb.processed = True
            fb.processed_at = datetime.utcnow()
        self.session.commit()

    def trending_problems(self, days: int = 30, threshold: int = 3) -> List[ProblemIdentification]:
        """Return problems whose frequency increased recently."""
        since = datetime.utcnow() - timedelta(days=days)
        return (
            self.session.query(ProblemIdentification)
            .filter(ProblemIdentification.last_reported >= since)
            .filter(ProblemIdentification.frequency_count >= threshold)
            .order_by(ProblemIdentification.frequency_count.desc())
            .all()
        )
