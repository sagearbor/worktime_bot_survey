from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON

from .app import Base


class ActivityLog(Base):
    """SQLAlchemy model representing a single activity log entry."""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    group_id = Column(String, nullable=False)
    activity = Column(String, nullable=False)
    sub_activity = Column(String, nullable=False)
    percent_work = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ActivityLog id={self.id} group_id={self.group_id} "
            f"activity={self.activity} sub_activity={self.sub_activity}>"
        )


class TimeAllocation(Base):
    """SQLAlchemy model representing a complete time allocation entry per person/department."""
    
    __tablename__ = "time_allocations"
    
    id = Column(Integer, primary_key=True)
    group_id = Column(String, nullable=False)
    activities = Column(JSON, nullable=False)  # {"Meeting": 25.5, "Research": 30.0, ...}
    feedback = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return (
            f"<TimeAllocation id={self.id} group_id={self.group_id} "
            f"activities={self.activities}>"
        )
