#!/bin/bash
# Start Celery Worker in background
celery -A app.worker.celery_app worker --loglevel=info &

# Start FastAPI App
uvicorn app.main:app --host 0.0.0.0 --port 7860
