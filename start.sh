#!/bin/bash

# Wait for database to be ready (optional, but recommended)
echo "Waiting for database..."
sleep 5

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Start the cron daemon
echo "Starting cron daemon..."
cron

# Start Gunicorn with optimized settings
echo "Starting Gunicorn..."
exec gunicorn fitness_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 4 \
    --worker-class=gthread \
    --worker-tmp-dir /dev/shm \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --timeout 180 \
    --log-level=info \
    --backlog=2048 \
    --worker-connections=1000 \
    --keep-alive=5