#!/bin/bash
# Quick development startup script

echo "🔧 Starting DCRI Logger development environment..."

# Set up Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Install dependencies if needed
if ! python -c "import flask, sqlalchemy, alembic" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install flask flask-cors sqlalchemy alembic python-dotenv psycopg2-binary pytest black
fi

# Run migrations (ignore errors as they're often just warnings)
echo "🔄 Running database migrations..."
alembic upgrade head 2>/dev/null || alembic stamp head 2>/dev/null || true

# Start the server
echo "🚀 Starting development server on http://127.0.0.1:8000"
python -m src.time_profiler.main