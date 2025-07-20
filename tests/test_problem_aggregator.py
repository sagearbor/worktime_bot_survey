from time_profiler import create_app, SessionLocal
from time_profiler.ai_insights import ProblemAggregator
from time_profiler import models


def setup_app(tmp_path):
    SessionLocal.remove()
    db_url = f"sqlite:///{tmp_path}/test.db"
    app = create_app({"TESTING": True, "DATABASE_URL": db_url})
    return app


def test_problem_aggregator_clusters(tmp_path):
    app = setup_app(tmp_path)
    aggregator = ProblemAggregator()

    aggregator.record_problem("The system crashes often")
    aggregator.record_problem("System crash occurs frequently")

    session = SessionLocal()
    problems = session.query(models.ProblemIdentification).all()
    session.close()
    assert len(problems) == 1
    assert problems[0].frequency_count == 2


def test_trending_problems(tmp_path):
    app = setup_app(tmp_path)
    aggregator = ProblemAggregator()
    for _ in range(3):
        aggregator.record_problem("Login fails on mobile")

    trending = aggregator.trending_problems(within_days=1, min_reports=2)
    assert trending

