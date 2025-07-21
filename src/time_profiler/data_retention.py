from __future__ import annotations

"""Utilities for data retention and summarization."""

from collections import defaultdict
from datetime import datetime
from typing import Dict

from .app import SessionLocal
from . import models


def summarize_entries(entries: list[models.UserSubmissionHistory]) -> Dict:
    """Return a summarized representation of the given submission entries."""
    if not entries:
        return {}

    subtype = entries[0].submission_type
    if subtype == "time_allocation":
        totals: Dict[str, float] = defaultdict(float)
        count = 0
        for e in entries:
            activities = e.submission_data.get("activities", {})
            for act, hrs in activities.items():
                totals[act] += hrs
            count += 1
        if count:
            return {act: hrs / count for act, hrs in totals.items()}
    elif subtype == "activity_log":
        counts: Dict[str, int] = defaultdict(int)
        for e in entries:
            act = e.submission_data.get("activity")
            if act:
                counts[act] += 1
        return counts
    return {"count": len(entries)}


def run_retention_tasks() -> None:
    """Archive old submissions and store summarized history."""
    session = SessionLocal()
    now = datetime.utcnow()
    try:
        distinct_pairs = (
            session.query(models.UserSubmissionHistory.user_id,
                          models.UserSubmissionHistory.submission_type)
            .distinct()
            .all()
        )
        for user_id, sub_type in distinct_pairs:
            records = (
                session.query(models.UserSubmissionHistory)
                .filter_by(user_id=user_id, submission_type=sub_type)
                .order_by(models.UserSubmissionHistory.timestamp.desc())
                .all()
            )
            if not records:
                continue
            latest = records[0]
            old = records[1:]
            if not old:
                continue
            summary_data = summarize_entries(old)
            summary = models.SubmissionSummary(
                user_id=user_id,
                submission_type=sub_type,
                summary_data=summary_data,
                start_period=min(e.timestamp for e in old),
                end_period=max(e.timestamp for e in old),
            )
            session.add(summary)
            for rec in old:
                rec.is_current = False
                rec.archived_at = now
        session.commit()
    finally:
        session.close()

