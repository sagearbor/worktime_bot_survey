from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .app import Base


class ActivityLog(Base):
    """SQLAlchemy model representing a single activity log entry."""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    group_id = Column(String, nullable=False)
    activity = Column(String, nullable=False)
    sub_activity = Column(String, nullable=False)
    hours_work = Column(Float, nullable=True)
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
    activities = Column(JSON, nullable=False)  # {"Meeting": 12.5, "Research": 20.0, ...} (hours per week)
    feedback = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return (
            f"<TimeAllocation id={self.id} group_id={self.group_id} "
            f"activities={self.activities}>"
        )


class UserSubmissionHistory(Base):
    """Track version/timestamp of each submission for temporal data management."""
    
    __tablename__ = "user_submission_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)  # User identifier (can be group_id for now)
    submission_type = Column(String, nullable=False)  # "time_allocation", "activity_log", "chatbot_feedback"
    submission_data = Column(JSON, nullable=False)  # Store the actual submission data
    version = Column(Integer, nullable=False, default=1)  # Version number for this user's submissions
    is_current = Column(Boolean, nullable=False, default=True)  # Flag for current/latest submission
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    archived_at = Column(DateTime, nullable=True)  # When this version was archived
    
    def __repr__(self) -> str:
        return (
            f"<UserSubmissionHistory id={self.id} user_id={self.user_id} "
            f"type={self.submission_type} version={self.version} current={self.is_current}>"
        )


class ChatbotFeedback(Base):
    """Store chatbot interactions and feedback from users."""
    
    __tablename__ = "chatbot_feedback"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    message_text = Column(Text, nullable=False)
    message_type = Column(String, nullable=False)  # "time_allocation", "problem_report", "success_story"
    processed = Column(Boolean, nullable=False, default=False)
    archived = Column(Boolean, nullable=False, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return (
            f"<ChatbotFeedback id={self.id} user_id={self.user_id} "
            f"type={self.message_type} processed={self.processed}>"
        )


class ProblemIdentification(Base):
    """Store identified problems from chatbot analysis."""
    
    __tablename__ = "problem_identification"
    
    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=True)  # Categorize problems for better analysis
    frequency_count = Column(Integer, nullable=False, default=1)
    first_reported = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_reported = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, nullable=False, default="identified")  # "identified", "analyzed", "escalated", "resolved"
    
    def __repr__(self) -> str:
        return (
            f"<ProblemIdentification id={self.id} description={self.description[:50]}... "
            f"frequency={self.frequency_count} status={self.status}>"
        )


class SolutionSuggestion(Base):
    """Store AI-generated solution suggestions for identified problems."""
    
    __tablename__ = "solution_suggestions"
    
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problem_identification.id"), nullable=False)
    description = Column(Text, nullable=False)
    estimated_effort = Column(String, nullable=True)  # "Low", "Medium", "High" or story points
    estimated_savings = Column(Float, nullable=True)  # Hours saved per week/month
    actual_savings = Column(Float, nullable=True)  # Real hours saved after implementation
    roi_score = Column(Float, nullable=True)  # Calculated ROI (savings/effort)
    status = Column(String, nullable=False, default="suggested")  # "suggested", "approved", "in_progress", "implemented", "rejected"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to problem
    problem = relationship("ProblemIdentification", backref="solutions")
    
    def __repr__(self) -> str:
        return (
            f"<SolutionSuggestion id={self.id} problem_id={self.problem_id} "
            f"effort={self.estimated_effort} status={self.status} "
            f"actual={self.actual_savings}>"
        )


class JiraTicketLifecycle(Base):
    """Track Jira ticket lifecycle for problems and solutions."""
    
    __tablename__ = "jira_ticket_lifecycle"
    
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problem_identification.id"), nullable=False)
    solution_id = Column(Integer, ForeignKey("solution_suggestions.id"), nullable=True)
    ticket_key = Column(String, nullable=False)  # Jira ticket key (e.g., "PROJ-123")
    ticket_url = Column(String, nullable=True)
    status = Column(String, nullable=False)  # Jira status (e.g., "Open", "In Progress", "Done")
    priority = Column(String, nullable=True)  # Jira priority
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    escalation_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    problem = relationship("ProblemIdentification", backref="jira_tickets")
    solution = relationship("SolutionSuggestion", backref="jira_tickets")
    
    def __repr__(self) -> str:
        return (
            f"<JiraTicketLifecycle id={self.id} ticket_key={self.ticket_key} "
            f"status={self.status} escalations={self.escalation_count}>"
        )
