"""Flask application factory and database setup."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

# SQLAlchemy setup
engine = None
SessionLocal = scoped_session(sessionmaker())
Base = declarative_base()


def load_config(config_path: Path) -> dict:
    """Load the DCRI configuration from a JSON file."""
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def init_db(database_url: str):
    """Initialize the database engine and session factory."""
    global engine
    engine = create_engine(database_url)
    SessionLocal.configure(bind=engine)


def create_app(config_object: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Default configuration
    app.config.setdefault("DATABASE_URL", "sqlite:///dcri_logger.db")
    default_config_path = Path(__file__).resolve().parents[2] / "config" / "dcri_config.json.example"
    app.config.setdefault("DCRI_CONFIG_PATH", default_config_path)

    if config_object:
        app.config.update(config_object)

    init_db(app.config["DATABASE_URL"])

    @app.route("/api/config", methods=["GET"])
    def get_config() -> jsonify:
        """Return configuration data loaded from the JSON file."""
        config_data = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
        return jsonify(config_data)

    @app.route("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app
