from __future__ import annotations

"""Jira integration helpers for ticket lifecycle management."""

from typing import Optional
import os
import requests


class JiraClient:
    """Lightweight Jira API client."""

    def __init__(self, base_url: str, user: str, api_token: str, project_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = (user, api_token)
        self.project_key = project_key

    def create_ticket(self, summary: str, description: str, issue_type: str = "Task") -> str:
        """Create a Jira ticket and return the ticket key."""
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
