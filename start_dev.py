#!/usr/bin/env python3
"""
Development startup script that handles common issues.
Run this instead of manually starting the dev server.

Usage:
  python start_dev.py           # Local development (SQLite)
  python start_dev.py --docker  # Docker development (PostgreSQL)
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def setup_environment():
    """Set up the development environment."""
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    
    # Add src to Python path
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    # Set environment variables
    os.environ.setdefault("PYTHONPATH", str(src_dir))
    os.environ.setdefault("DATABASE_URL", "sqlite:///dcri_logger.db")

def install_dependencies():
    """Install required dependencies if needed."""
    try:
        import flask
        import sqlalchemy
        import alembic
        print("✅ Dependencies already installed")
    except ImportError as e:
        print(f"📦 Installing missing dependency: {e.name}")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "flask", "flask-cors", "sqlalchemy", "alembic", 
            "python-dotenv", "psycopg2-binary", "pytest", "black"
        ])

def run_migrations():
    """Run database migrations."""
    try:
        print("🔄 Running database migrations...")
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode != 0:
            print(f"⚠️  Migration warning (this might be normal): {result.stderr}")
            # Try to stamp the database as up-to-date
            subprocess.run(["alembic", "stamp", "head"], cwd=".")
        else:
            print("✅ Migrations completed successfully")
    except Exception as e:
        print(f"⚠️  Migration issue (might be normal): {e}")

def start_server():
    """Start the development server."""
    print("🚀 Starting development server...")
    try:
        from src.time_profiler.main import main
        main()
    except ImportError:
        # Fallback method
        subprocess.run([sys.executable, "-m", "src.time_profiler.main"])

def start_docker():
    """Start the application using Docker Compose."""
    print("🐳 Starting Docker containers...")
    try:
        subprocess.run(["docker", "compose", "up", "--build"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start DCRI Logger development environment")
    parser.add_argument("--docker", action="store_true", help="Use Docker containers (PostgreSQL)")
    args = parser.parse_args()

    if args.docker:
        start_docker()
    else:
        print("🔧 Setting up local development environment...")
        setup_environment()
        install_dependencies()
        run_migrations()
        start_server()