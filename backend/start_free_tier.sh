#!/bin/bash

# 1. Start Embedded Redis (Unlimited, Local)
echo "Starting Local Redis..."
redis-server --daemonize yes

# Override config to use Local Redis
export REDIS_URL="redis://localhost:6379/0"

# 2. Start Celery Worker
celery -A app.core.celery_app worker --loglevel=info &

# Start FastAPI App
uvicorn app.main:app --host 0.0.0.0 --port 7860
