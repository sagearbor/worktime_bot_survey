"""AI insights and analysis tools."""

from .problem_analyzer import ProblemAggregator
from .jira_integration import (
    JiraClient,
    MCPJiraClient,
    create_ticket_if_not_exists,
    escalate_ticket,
    archive_and_create_new_ticket,
    update_solution_impact,
)
from .solution_engine import (
    SolutionEngine,
    estimate_effort,
    calculate_roi,
    prioritize_solutions,
)

__all__ = [
    "ProblemAggregator",
    "JiraClient",
    "MCPJiraClient",
    "create_ticket_if_not_exists",
    "escalate_ticket",
    "archive_and_create_new_ticket",
    "update_solution_impact",
    "SolutionEngine",
    "estimate_effort",
    "calculate_roi",
    "prioritize_solutions",
]
