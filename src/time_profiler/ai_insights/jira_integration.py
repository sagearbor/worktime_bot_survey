from __future__ import annotations

"""Jira integration helpers for ticket lifecycle management."""

from typing import Optional
from datetime import datetime
import os
import requests

from .. import models
from ..app import SessionLocal


class JiraClient:
    """Lightweight Jira API client with optional MCP support."""

    def __init__(self, base_url: str, user: str, api_token: str, project_key: str, mcp_endpoint: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = (user, api_token)
        self.project_key = project_key
        self.mcp_endpoint = (mcp_endpoint or os.getenv("MCP_ENDPOINT", "")).rstrip("/") if (mcp_endpoint or os.getenv("MCP_ENDPOINT")) else None

    def create_ticket(self, summary: str, description: str, issue_type: str = "Task") -> str:
        """Create a Jira ticket and return the ticket key."""
        if self.mcp_endpoint:
            payload = {
                "action": "create_ticket",
                "data": {
                    "project_key": self.project_key,
                    "summary": summary,
                    "description": description,
                    "issue_type": issue_type,
                },
            }
            response = requests.post(self.mcp_endpoint, json=payload, timeout=10)
            if response.status_code != 200:
                raise RuntimeError(f"MCP ticket creation failed: {response.text}")
            data = response.json()
            if not data.get("ticket_key"):
                raise RuntimeError("Invalid MCP response")
            return data["ticket_key"]
        url = f"{self.base_url}/rest/api/2/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }
        }
        response = requests.post(url, json=payload, auth=self.auth, timeout=10)
        if response.status_code != 201:
            raise RuntimeError(f"Failed to create ticket: {response.text}")
        return response.json().get("key")

    def transition_ticket(self, ticket_key: str, transition_id: str) -> None:
        """Transition a Jira ticket to a new state."""
        if self.mcp_endpoint:
            payload = {
                "action": "transition_ticket",
                "data": {"ticket_key": ticket_key, "transition_id": transition_id},
            }
            response = requests.post(self.mcp_endpoint, json=payload, timeout=10)
            if response.status_code != 200:
                raise RuntimeError(f"MCP transition failed: {response.text}")
            return
        url = f"{self.base_url}/rest/api/2/issue/{ticket_key}/transitions"
        payload = {"transition": {"id": transition_id}}
        response = requests.post(url, json=payload, auth=self.auth, timeout=10)
        if response.status_code not in {200, 204}:
            raise RuntimeError(f"Failed to transition ticket: {response.text}")


class MCPJiraClient(JiraClient):
    """Jira client that communicates via Model Context Protocol (MCP)."""

    def __init__(self, base_url: str, user: str, api_token: str, project_key: str, mcp_endpoint: str) -> None:
        super().__init__(base_url, user, api_token, project_key)
        self.mcp_endpoint = mcp_endpoint.rstrip("/")

    def create_ticket_via_mcp(self, summary: str, description: str, issue_type: str = "Task") -> str:
        """Request ticket creation through an MCP endpoint."""
        payload = {
            "action": "create_ticket",
            "data": {
                "project_key": self.project_key,
                "summary": summary,
                "description": description,
                "issue_type": issue_type,
            },
        }
        response = requests.post(self.mcp_endpoint, json=payload, timeout=10)
        if response.status_code != 200:
            raise RuntimeError(f"MCP ticket creation failed: {response.text}")
        data = response.json()
        if not data.get("ticket_key"):
            raise RuntimeError("Invalid MCP response")
        return data["ticket_key"]

    def transition_ticket_via_mcp(self, ticket_key: str, transition_id: str) -> None:
        """Request a ticket transition through MCP."""
        payload = {
            "action": "transition_ticket",
            "data": {"ticket_key": ticket_key, "transition_id": transition_id},
        }
        response = requests.post(self.mcp_endpoint, json=payload, timeout=10)
        if response.status_code != 200:
            raise RuntimeError(f"MCP transition failed: {response.text}")


def create_ticket_if_not_exists(session, client: JiraClient, problem_id: int, summary: str, description: str, issue_type: str = "Task") -> models.JiraTicketLifecycle:
    """Create a ticket for a problem if one doesn't already exist."""
    ticket = session.query(models.JiraTicketLifecycle).filter_by(problem_id=problem_id, status="Open").first()
    if ticket:
        return ticket
    key = client.create_ticket(summary, description, issue_type)
    ticket = models.JiraTicketLifecycle(
        problem_id=problem_id,
        ticket_key=key,
        status="Open",
        priority="Low",
    )
    session.add(ticket)
    session.commit()
    return ticket


def escalate_ticket(session, client: JiraClient, ticket: models.JiraTicketLifecycle, new_priority: str) -> None:
    """Increase ticket priority and record escalation."""
    if ticket.priority == new_priority:
        return
    client.transition_ticket(ticket.ticket_key, "escalate")
    ticket.priority = new_priority
    ticket.escalation_count += 1
    ticket.last_updated = datetime.utcnow()
    session.commit()


def archive_and_create_new_ticket(session, client: JiraClient, ticket: models.JiraTicketLifecycle, summary: str, description: str, priority: str = "High") -> models.JiraTicketLifecycle:
    """Close an old ticket and open a new escalated one."""
    client.transition_ticket(ticket.ticket_key, "close")
    ticket.status = "Closed"
    ticket.last_updated = datetime.utcnow()
    session.commit()
    new_ticket = client.create_ticket(summary, description)
    new = models.JiraTicketLifecycle(
        problem_id=ticket.problem_id,
        ticket_key=new_ticket,
        status="Open",
        priority=priority,
        escalation_count=ticket.escalation_count + 1,
    )
    session.add(new)
    session.commit()
    return new


def update_solution_impact(session, solution_id: int, actual_savings: float) -> models.SolutionSuggestion:
    """Record the real savings achieved by a solution."""
    solution = session.query(models.SolutionSuggestion).filter_by(id=solution_id).first()
    if not solution:
        raise ValueError("Solution not found")
    solution.actual_savings = actual_savings
    session.commit()
    return solution

