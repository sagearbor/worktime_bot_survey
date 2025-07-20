"""Flask application factory and database setup."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

# SQLAlchemy setup
engine = None
SessionLocal = scoped_session(sessionmaker())
Base = declarative_base()

# Import models so they are registered with SQLAlchemy's metadata
from . import models  # noqa: F401


def load_config(config_path: Path) -> dict:
    """Load the DCRI configuration from a JSON file."""
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def init_db(database_url: str):
    """Initialize the database engine and session factory."""
    global engine
    engine = create_engine(database_url)
    SessionLocal.remove()
    SessionLocal.configure(bind=engine)
    # Ensure tables are created when running without migrations
    Base.metadata.create_all(bind=engine)


def create_app(config_object: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder='../../templates')
    
    # Enable CORS for all routes
    CORS(app)

    # Default configuration
    app.config.setdefault("DATABASE_URL", "sqlite:///dcri_logger.db")
    default_config_path = (
        Path(__file__).resolve().parents[2] / "config" / "dcri_config.json.example"
    )
    app.config.setdefault("DCRI_CONFIG_PATH", default_config_path)

    if config_object:
        app.config.update(config_object)

    init_db(app.config["DATABASE_URL"])

    @app.route("/api/config", methods=["GET"])
    def get_config() -> jsonify:
        """Return configuration data loaded from the JSON file."""
        config_data = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
        return jsonify(config_data)

    @app.route("/api/submit", methods=["POST"])
    def submit_activity() -> jsonify:
        """Receive and validate an activity log submission."""
        data = request.get_json(silent=True) or {}

        required = ["group_id", "activity", "sub_activity"]
        if not all(data.get(f) for f in required):
            return jsonify({"error": "Missing required fields"}), 400

        config = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
        valid_groups = {g["id"] for g in config.get("groups", [])}
        if data["group_id"] not in valid_groups:
            return jsonify({"error": "Invalid group_id"}), 400

        activity_map = {
            a["category"]: set(a.get("sub_activities", []))
            for a in config.get("activities", [])
        }
        if data["activity"] not in activity_map:
            return jsonify({"error": "Invalid activity"}), 400

        sub_acts = activity_map[data["activity"]]
        if sub_acts and data["sub_activity"] not in sub_acts:
            return jsonify({"error": "Invalid sub_activity"}), 400

        session = SessionLocal()
        try:
            feedback_text = None
            if config.get("enableFreeTextFeedback"):
                feedback_text = data.get("feedback")

            log_entry = models.ActivityLog(
                group_id=data["group_id"],
                activity=data["activity"],
                sub_activity=data["sub_activity"],
                percent_work=data.get("percent_work"),
                feedback=feedback_text,
            )
            session.add(log_entry)
            session.commit()
            return jsonify({"status": "success", "id": log_entry.id})
        except Exception:  # pragma: no cover - unexpected DB errors
            session.rollback()
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/results", methods=["GET"])
    def get_results() -> jsonify:
        """Return aggregated submission counts by group and activity."""
        session = SessionLocal()
        try:
            query = session.query(
                models.ActivityLog.group_id,
                models.ActivityLog.activity,
                func.count(models.ActivityLog.id).label("count"),
            )

            # Optional filters
            group_id = request.args.get("group_id")
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")

            if group_id:
                query = query.filter(models.ActivityLog.group_id == group_id)

            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    query = query.filter(models.ActivityLog.timestamp >= start_dt)
                except ValueError:
                    return jsonify({"error": "Invalid start_date"}), 400

            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date)
                    query = query.filter(models.ActivityLog.timestamp <= end_dt)
                except ValueError:
                    return jsonify({"error": "Invalid end_date"}), 400

            rows = (
                query.group_by(models.ActivityLog.group_id, models.ActivityLog.activity).all()
            )

            results = [
                {
                    "group_id": r.group_id,
                    "activity": r.activity,
                    "count": r.count,
                }
                for r in rows
            ]
            return jsonify(results)
        except Exception:  # pragma: no cover - unexpected DB errors
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.route("/")
    def index():
        """Serve the main survey page."""
        return render_template("index.html")
    
    @app.route("/dashboard")
    def dashboard():
        """Serve the dashboard page."""
        return render_template("dashboard.html")

    return app
