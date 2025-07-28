#!/bin/bash

# Run Celery workers for GHG Calculator

echo "Starting Celery workers..."

# Start worker for calculations queue
celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queue=calculations \
    --hostname=worker1@%h &

# Start worker for reports queue
celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queue=reports \
    --hostname=worker2@%h &

# Start worker for imports queue
celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queue=imports \
    --hostname=worker3@%h &

# Start Celery beat for scheduled tasks
celery -A app.tasks.celery_app beat --loglevel=info &

echo "Celery workers started!"
echo "Press Ctrl+C to stop all workers"

# Wait for interrupt
wait
