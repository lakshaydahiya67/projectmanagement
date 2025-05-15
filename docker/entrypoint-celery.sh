#!/bin/bash

set -e

# Wait for Redis to be ready
./docker/wait-for-it.sh ${REDIS_HOST:-redis}:${REDIS_PORT:-6379} -t 60

# Wait for the backend to be ready
./docker/wait-for-it.sh backend:8000 -t 60

# Start the Celery worker
echo "Starting Celery worker..."
exec celery -A projectmanagement worker --loglevel=info 