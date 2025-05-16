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

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if needed (non-interactively)
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
            username='admin',
            email='admin@example.com',
            password='adminpassword', 
            first_name='Admin', 
            last_name='User'
        )
        print('Superuser created successfully.')
    except Exception as e:
        print(f'Error creating superuser: {e}')
else:
    print('Superuser already exists.')
"

# Start the Django application
echo "Starting Django application..."
exec daphne -b 0.0.0.0 -p 8000 projectmanagement.asgi:application 