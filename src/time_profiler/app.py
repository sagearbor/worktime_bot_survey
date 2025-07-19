from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

# SQLAlchemy setup
engine = None
SessionLocal = scoped_session(sessionmaker())
Base = declarative_base()


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

    if config_object:
        app.config.update(config_object)

    init_db(app.config["DATABASE_URL"])

    @app.route("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app
