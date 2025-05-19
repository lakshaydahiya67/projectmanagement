#!/bin/bash

echo "Creating the staticfiles directory with correct permissions..."
docker exec -u root backend mkdir -p /app/staticfiles
docker exec -u root backend chmod -R 777 /app/staticfiles

echo "Running collectstatic command..."
docker exec -u root backend python manage.py collectstatic --noinput

echo "Setting correct permissions on collected files..."
docker exec -u root backend chmod -R 755 /app/staticfiles

echo "Restarting the frontend container to pick up the changes..."
docker restart frontend

echo "Done! Static files should now be properly accessible."
