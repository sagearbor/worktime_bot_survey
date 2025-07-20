from datetime import datetime, timedelta

from time_profiler import create_app, SessionLocal, models


def setup_app(tmp_path):
    SessionLocal.remove()
    db_url = f"sqlite:///{tmp_path}/test.db"
    return create_app({"TESTING": True, "DATABASE_URL": db_url})


def test_update_problem_status(tmp_path):
    app = setup_app(tmp_path)
    client = app.test_client()

    session = SessionLocal()
    problem = models.ProblemIdentification(description="Bug")
    session.add(problem)
    session.commit()
    pid = problem.id
    session.close()

    resp = client.patch(f"/api/problems/{pid}", json={"status": "approved"})
    assert resp.status_code == 200

    session = SessionLocal()
    updated = session.query(models.ProblemIdentification).get(pid)
    session.close()
    assert updated.status == "approved"


def test_archive_endpoint(tmp_path):
    app = setup_app(tmp_path)
    client = app.test_client()

    session = SessionLocal()
    old = models.ChatbotFeedback(
        user_id="u1",
        message_text="hi",
        message_type="general",
        processed=True,
        timestamp=datetime.utcnow() - timedelta(days=10),
    )
    session.add(old)
    session.commit()
    session.close()

    resp = client.post("/api/admin/archive?days=0")
    assert resp.status_code == 200

    session = SessionLocal()
    archived = session.query(models.ChatbotFeedback).first()
    session.close()
    assert archived.archived is True
