"""Utilities to enforce data retention policies."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import UserSubmissionHistory


RETENTION_DAYS = 180


def enforce_latest_submission_policy(session: Session) -> None:
    """Keep only the latest submission per user and type as current."""
    subtypes = session.query(UserSubmissionHistory.submission_type).distinct()
    for (stype,) in subtypes:
        users = session.query(UserSubmissionHistory.user_id).filter_by(submission_type=stype).distinct()
        for (user_id,) in users:
            latest = (
                session.query(UserSubmissionHistory)
                .filter_by(user_id=user_id, submission_type=stype)
                .order_by(UserSubmissionHistory.timestamp.desc())
                .first()
            )
            others = (
                session.query(UserSubmissionHistory)
                .filter_by(user_id=user_id, submission_type=stype)
                .filter(UserSubmissionHistory.id != latest.id)
                .all()
            )
            for entry in others:
                if entry.is_current:
                    entry.is_current = False
                    entry.archived_at = datetime.utcnow()
    session.commit()


def archive_old_entries(session: Session, days: int = RETENTION_DAYS) -> None:
    """Archive submissions older than the retention window."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    old_entries = session.query(UserSubmissionHistory).filter(UserSubmissionHistory.timestamp < cutoff).all()
    for entry in old_entries:
        entry.is_current = False
        entry.archived_at = entry.archived_at or datetime.utcnow()
    session.commit()
