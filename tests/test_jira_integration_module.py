import json
from unittest.mock import patch
from time_profiler import create_app, SessionLocal, models
from time_profiler.ai_insights import (
    JiraClient,
    MCPJiraClient,
    create_ticket_if_not_exists,
    escalate_ticket,
    archive_and_create_new_ticket,
    update_solution_impact,
)


def setup_app(tmp_path):
    SessionLocal.remove()
    db_url = f"sqlite:///{tmp_path}/test.db"
    app = create_app({"TESTING": True, "DATABASE_URL": db_url})
    return app


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


def test_create_ticket_if_not_exists(tmp_path):
    app = setup_app(tmp_path)
    client = JiraClient("https://jira.example.com", "user", "token", "PROJ")

    session = SessionLocal()
    problem = models.ProblemIdentification(description="Bug")
    session.add(problem)
    session.commit()
    problem_id = problem.id
    session.close()

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"key": "PROJ-1"}
        session = SessionLocal()
        ticket1 = create_ticket_if_not_exists(session, client, problem_id, "Bug", "Details")
        ticket2 = create_ticket_if_not_exists(session, client, problem_id, "Bug", "Details")
        session.close()
        assert ticket1.ticket_key == "PROJ-1"
        assert ticket1.id == ticket2.id
        assert mock_post.call_count == 1


def test_escalate_and_archive(tmp_path):
    app = setup_app(tmp_path)
    client = JiraClient("https://jira.example.com", "user", "token", "PROJ")

    session = SessionLocal()
    problem = models.ProblemIdentification(description="Bug")
    session.add(problem)
    session.commit()
    problem_id = problem.id
    ticket = models.JiraTicketLifecycle(problem_id=problem_id, ticket_key="PROJ-1", status="Open", priority="Low")
    session.add(ticket)
    session.commit()
    ticket_id = ticket.id
    session.close()

    with patch("requests.post") as mock_post:
        # first two calls for transitions return 200, final call for new ticket returns 201
        mock_post.side_effect = [
            type("Resp", (), {"status_code": 200, "text": "ok"})(),
            type("Resp", (), {"status_code": 200, "text": "ok"})(),
            type("Resp", (), {"status_code": 201, "json": lambda self=None: {"key": "PROJ-2"}})(),
        ]
        # escalate priority
        session = SessionLocal()
        ticket_obj = session.get(models.JiraTicketLifecycle, ticket_id)
        escalate_ticket(session, client, ticket_obj, "High")
        session.refresh(ticket_obj)
        assert ticket_obj.priority == "High"
        assert ticket_obj.escalation_count == 1
        # archive and create new
        new_ticket = archive_and_create_new_ticket(session, client, ticket_obj, "Escalated bug", "Details")
        assert ticket_obj.status == "Closed"
        assert new_ticket.ticket_key == "PROJ-2"
        session.close()


def test_update_solution_impact(tmp_path):
    app = setup_app(tmp_path)
    session = SessionLocal()
    problem = models.ProblemIdentification(description="Bug")
    session.add(problem)
    session.commit()
    solution = models.SolutionSuggestion(problem_id=problem.id, description="Fix", estimated_savings=5)
    session.add(solution)
    session.commit()
    update_solution_impact(session, solution.id, 8)
    session.refresh(solution)
    assert solution.actual_savings == 8

