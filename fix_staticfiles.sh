#!/bin/bash

# Script to fix static files permissions and collection
echo "Creating staticfiles directory if it doesn't exist..."
docker exec -it backend mkdir -p /app/staticfiles

echo "Setting permissions for the staticfiles directory..."
docker exec -it backend bash -c "chmod -R 777 /app/staticfiles"

echo "Collecting static files..."
docker exec -it backend python manage.py collectstatic --noinput

echo "Done!"
