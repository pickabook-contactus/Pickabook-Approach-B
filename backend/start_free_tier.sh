#!/bin/bash

# Run DB Migrations
echo "Running DB Migrations..."
# python -m app.db.init_db # Skipped: Module not found, using migrate_db.py instead 
# Check main.py. It typically calls Base.metadata.create_all(bind=engine).
# If correct, we don't need manual migration for tables, BUT we might need data/columns.
# Let's rely on 'python migrate_db.py' if it exists and works.
python migrate_db.py

# Start Celery Worker in background
# --concurrency=1 to save memory on free tier
echo "Starting Celery Worker..."
celery -A app.core.celery_app worker --loglevel=info --concurrency=1 &

# Start FastAPI Backend in foreground
echo "Starting FastAPI Backend..."
# Default to 7860 (Hugging Face) if PORT is not set
export PORT=${PORT:-7860}
uvicorn app.main:app --host 0.0.0.0 --port $PORT
