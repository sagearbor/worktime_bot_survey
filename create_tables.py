#!/usr/bin/env python3
"""Create database tables for the DCRI Time Profiler application."""

from src.time_profiler import create_app

def create_all_tables():
    """Create all database tables."""
    # Create the Flask app - this automatically calls init_db() which creates tables
    app = create_app()
    print("Successfully initialized database and created all tables!")

if __name__ == "__main__":
    create_all_tables()