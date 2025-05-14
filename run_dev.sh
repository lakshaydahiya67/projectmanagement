#!/bin/bash

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Making migrations for each app..."
python manage.py makemigrations users
python manage.py makemigrations organizations
python manage.py makemigrations projects
python manage.py makemigrations tasks
python manage.py makemigrations notifications
python manage.py makemigrations analytics
python manage.py makemigrations activitylogs

echo "Applying migrations..."
python manage.py migrate

# Check if superuser needs to be created
echo "Checking if superuser exists..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin@example.com', 'adminpassword', first_name='Admin', last_name='User')
    print('Superuser created successfully.')
else:
    print('Superuser already exists.')
"

echo "Starting development server..."
python manage.py runserver 