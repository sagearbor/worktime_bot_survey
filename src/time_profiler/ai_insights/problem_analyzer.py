"""Simple problem aggregation and trending issue detection."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Iterable, List, Tuple

from ..models import ProblemIdentification
from ..app import SessionLocal


class ProblemAggregator:
    """Aggregate problem reports and track trends."""

    def __init__(self, similarity_threshold: float = 0.25):
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        words = re.findall(r"\w+", text.lower())
        normalized = []
        for w in words:
            if w.endswith("es"):
                w = w[:-2]
            elif w.endswith("s"):
                w = w[:-1]
            normalized.append(w)
        return set(normalized)

    def _similar(self, a: str, b: str) -> bool:
        ta, tb = self._tokenize(a), self._tokenize(b)
        if not ta or not tb:
            return False
        intersect = ta.intersection(tb)
        denom = min(len(ta), len(tb))
        if denom == 0:
            return False
        return len(intersect) / denom >= self.similarity_threshold

    def record_problem(self, description: str) -> ProblemIdentification:
        """Record a problem report, incrementing frequency if similar exists."""
        session = SessionLocal()
        try:
            for problem in session.query(ProblemIdentification).all():
                if self._similar(problem.description, description):
                    problem.frequency_count += 1
                    problem.last_reported = datetime.utcnow()
                    session.commit()
                    return problem
            new_problem = ProblemIdentification(description=description)
            session.add(new_problem)
            session.commit()
            return new_problem
        finally:
            session.close()

    def trending_problems(self, within_days: int = 7, min_reports: int = 3) -> List[Tuple[int, str, int]]:
        """Return problems reported frequently in recent period."""
        session = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=within_days)
            problems = (
                session.query(ProblemIdentification)
                .filter(ProblemIdentification.last_reported >= cutoff)
                .all()
            )
            results: List[Tuple[int, str, int]] = []
            for p in problems:
                if p.frequency_count >= min_reports:
                    results.append((p.id, p.description, p.frequency_count))
            return results
        finally:
            session.close()

