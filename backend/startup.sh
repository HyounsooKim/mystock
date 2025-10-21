#!/bin/bash

# Azure App Service Startup Script for MyStock Backend

echo "Starting MyStock Backend..."

# Install dependencies
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application with Gunicorn
echo "Starting Gunicorn..."
gunicorn src.main:app \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
