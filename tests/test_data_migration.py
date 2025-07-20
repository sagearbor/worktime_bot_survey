from time_profiler import create_app, SessionLocal
from time_profiler import models
from time_profiler.data_migration import migrate_activity_logs_to_time_allocations


def setup_app(tmp_path):
    SessionLocal.remove()
    db_url = f"sqlite:///{tmp_path}/test.db"
    app = create_app({"TESTING": True, "DATABASE_URL": db_url})
    return app


def test_migrate_activity_logs(tmp_path):
    app = setup_app(tmp_path)
    session = SessionLocal()
    session.add(models.ActivityLog(group_id="g1", activity="Dev", sub_activity="A"))
    session.add(models.ActivityLog(group_id="g1", activity="Dev", sub_activity="B"))
    session.commit()
    session.close()

    migrate_activity_logs_to_time_allocations()

    session = SessionLocal()
    allocations = session.query(models.TimeAllocation).all()
    session.close()
    assert allocations
    assert allocations[0].activities["Dev"] == 2.0

