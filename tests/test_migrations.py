from pathlib import Path
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command


def test_run_migrations(tmp_path):
    """Ensure Alembic migrations run and create the activity_logs table."""
    db_path = tmp_path / "test.db"
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)
    assert "activity_logs" in inspector.get_table_names()

