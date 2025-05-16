#!/bin/bash

set -e

# Wait for Redis to be ready
./docker/wait-for-it.sh ${REDIS_HOST:-redis}:${REDIS_PORT:-6379} -t 60

# Test email configuration if using SMTP
if [ "$EMAIL_BACKEND" = "django.core.mail.backends.smtp.EmailBackend" ]; then
    echo "Testing email configuration..."
    python -m email_test admin@example.com || {
        echo "Warning: Email configuration test failed but continuing startup"
    }
fi

# Ensure proper directory permissions for SQLite
if [ -n "$DATABASE_PATH" ]; then
    mkdir -p $(dirname "$DATABASE_PATH")
    touch "$DATABASE_PATH"
    chown -R appuser:appuser $(dirname "$DATABASE_PATH")
fi

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if needed (non-interactively)
# Using environment variables for credentials instead of hardcoding
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    try:
        User.objects.create_superuser(
            username=os.environ.get('DJANGO_SUPERUSER_USERNAME'),
            email=os.environ.get('DJANGO_SUPERUSER_EMAIL'),
            password=os.environ.get('DJANGO_SUPERUSER_PASSWORD'), 
            first_name=os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Admin'), 
            last_name=os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'User')
        )
        print('Superuser created successfully.')
    except Exception as e:
        print(f'Error creating superuser: {e}')
else:
    print('Superuser already exists.')
"
else
    echo "Skipping superuser creation (environment variables not set)"
fi

# Start the Django application
echo "Starting Django application..."
exec daphne -b 0.0.0.0 -p 8000 projectmanagement.asgi:application 