from pathlib import Path
from time_profiler import create_app, SessionLocal, models
from time_profiler.app import load_config


def setup_app(tmp_path):
    SessionLocal.remove()
    db_url = f"sqlite:///{tmp_path}/test.db"
    app = create_app({"TESTING": True, "DATABASE_URL": db_url})
    return app


def test_jira_webhook_update(tmp_path):
    app = setup_app(tmp_path)
    client = app.test_client()

    session = SessionLocal()
    problem = models.ProblemIdentification(description="Bug")
    session.add(problem)
    session.commit()
    ticket = models.JiraTicketLifecycle(problem_id=problem.id, ticket_key="PROJ-1", status="Open")
    session.add(ticket)
    session.commit()
    session.close()

    resp = client.post("/api/jira-webhook", json={"ticket_key": "PROJ-1", "status": "In Progress"})
    assert resp.status_code == 200

    session = SessionLocal()
    updated = session.query(models.JiraTicketLifecycle).first()
    session.close()
    assert updated.status == "In Progress"
