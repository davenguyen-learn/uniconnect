#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
