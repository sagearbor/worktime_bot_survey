from time_profiler.ai_insights import (
    SolutionEngine,
    estimate_effort,
    calculate_roi,
    prioritize_solutions,
)
from time_profiler import create_app, SessionLocal, models


def setup_app(tmp_path):
    SessionLocal.remove()
    db_url = f"sqlite:///{tmp_path}/test.db"
    return create_app({"TESTING": True, "DATABASE_URL": db_url})


def test_suggestion_fallback(tmp_path):
    setup_app(tmp_path)
    engine = SolutionEngine(api_key=None)
    suggestions = engine.suggest("App crashes when saving files", max_suggestions=2)
    assert len(suggestions) == 2
    assert all(isinstance(s, str) for s in suggestions)


def test_effort_and_roi(tmp_path):
    setup_app(tmp_path)
    effort = estimate_effort("Short fix")
    assert effort == "Low"
    roi = calculate_roi(10, effort, people_affected=5)
    assert roi == 50

    session = SessionLocal()
    problem = models.ProblemIdentification(description="Bug")
    session.add(problem)
    session.commit()
    solution1 = models.SolutionSuggestion(
        problem_id=problem.id,
        description="Fix bug",
        estimated_effort="Low",
        estimated_savings=5,
        roi_score=calculate_roi(5, "Low", 1),
    )
    solution2 = models.SolutionSuggestion(
        problem_id=problem.id,
        description="Rewrite module",
        estimated_effort="High",
        estimated_savings=20,
        roi_score=calculate_roi(20, "High", 1),
    )
    session.add_all([solution1, solution2])
    session.commit()
    ordered = prioritize_solutions([solution1, solution2])
    assert ordered[0].roi_score >= ordered[1].roi_score
    session.close()
