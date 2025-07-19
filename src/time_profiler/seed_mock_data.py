import json
from pathlib import Path
from . import create_app, SessionLocal, models


def seed_from_file(data_path: Path, db_url: str | None = None) -> None:
    """Seed the database with mock ActivityLog entries."""
    app_config = {}
    if db_url:
        app_config["DATABASE_URL"] = db_url
    app = create_app(app_config)

    with data_path.open("r", encoding="utf-8") as f:
        entries = json.load(f)

    session = SessionLocal()
    try:
        for item in entries:
            log = models.ActivityLog(
                group_id=item["group_id"],
                activity=item["activity"],
                sub_activity=item["sub_activity"],
            )
            session.add(log)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed mock activity log data")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "config"
        / "mock_activity_logs.json",
        help="Path to JSON file with mock data",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default="sqlite:///dcri_logger.db",
        help="Database URL",
    )
    args = parser.parse_args()

    seed_from_file(args.data, args.db_url)
