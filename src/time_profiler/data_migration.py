"""Utilities for migrating legacy data to the new schema."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict

from .app import SessionLocal
from . import models


def migrate_activity_logs_to_time_allocations() -> None:
    """Convert ActivityLog records into summarized TimeAllocation entries."""
    session = SessionLocal()
    try:
        grouped: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for log in session.query(models.ActivityLog).all():
            grouped[log.group_id][log.activity] += 1.0

        for group_id, activities in grouped.items():
            allocation = models.TimeAllocation(group_id=group_id, activities=dict(activities))
            session.add(allocation)

        session.commit()
    finally:
        session.close()


def export_time_allocations() -> Dict[str, Dict[str, float]]:
    """Export all time allocations as a nested dictionary."""
    session = SessionLocal()
    try:
        data = {}
        for entry in session.query(models.TimeAllocation).all():
            data.setdefault(entry.group_id, []).append(entry.activities)
        return data
    finally:
        session.close()

