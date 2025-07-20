from time_profiler import create_app, SessionLocal
from time_profiler import models


def setup_app(tmp_path):
    SessionLocal.remove()
    db_url = f"sqlite:///{tmp_path}/test.db"
    app = create_app({"TESTING": True, "DATABASE_URL": db_url})
    return app


def test_insights_endpoint(tmp_path):
    app = setup_app(tmp_path)
    client = app.test_client()

    session = SessionLocal()
    problem = models.ProblemIdentification(description="Server crash", frequency_count=3)
    session.add(problem)
    session.commit()
    solution = models.SolutionSuggestion(problem_id=problem.id, description="Fix bug", status="implemented", actual_savings=5, roi_score=1.2)
    session.add(solution)
    session.add(models.ChatbotFeedback(user_id="u1", message_text="Great job", message_type="success_story"))
    session.commit()
    session.close()

    resp = client.get("/api/insights")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "problem_stats" in data
    assert "solution_stats" in data
    assert data["problem_stats"]["total"] == 1
    assert data["solution_stats"]["total"] == 1
