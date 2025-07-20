import json
from pathlib import Path
from . import create_app, SessionLocal, models


def seed_allocation_from_file(data_path: Path, db_url: str | None = None) -> None:
    """Seed the database with mock TimeAllocation entries."""
    app_config = {}
    if db_url:
        app_config["DATABASE_URL"] = db_url
    app = create_app(app_config)

    with data_path.open("r", encoding="utf-8") as f:
        entries = json.load(f)

    session = SessionLocal()
    try:
        for item in entries:
            allocation = models.TimeAllocation(
                group_id=item["group_id"],
                activities=item["activities"],
                feedback=item.get("feedback"),
            )
            session.add(allocation)
        session.commit()
        print(f"Successfully added {len(entries)} time allocation entries")
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed mock time allocation data")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "config"
        / "mock_time_allocations.json",
        help="Path to JSON file with mock allocation data",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default="sqlite:///dcri_logger.db",
        help="Database URL",
    )
    args = parser.parse_args()

    seed_allocation_from_file(args.data, args.db_url)