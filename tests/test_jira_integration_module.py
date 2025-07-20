import json
from unittest.mock import patch
from time_profiler.ai_insights.jira_integration import JiraClient, MCPJiraClient


def test_jira_client_create_ticket_success():
    client = JiraClient("https://jira.example.com", "user", "token", "PROJ")
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"key": "PROJ-1"}
        key = client.create_ticket("Bug found", "Details")
        assert key == "PROJ-1"
        payload = mock_post.call_args.kwargs["json"]
        assert payload["fields"]["project"]["key"] == "PROJ"


def test_mcp_jira_client_create_ticket_via_mcp():
    client = MCPJiraClient(
        "https://jira.example.com",
        "user",
        "token",
        "PROJ",
        "https://mcp.example.com/agent",
    )
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ticket_key": "PROJ-2"}
        key = client.create_ticket_via_mcp("Issue", "More info")
        assert key == "PROJ-2"
        payload = mock_post.call_args.kwargs["json"]
        assert payload["action"] == "create_ticket"
