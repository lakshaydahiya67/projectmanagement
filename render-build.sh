#!/bin/bash

# Exit on error and print commands as they are executed
set -ex

export DJANGO_SETTINGS_MODULE="projectmanagement.settings.production"

# Install Python dependencies
echo "=== Installing Python dependencies ==="
python -m pip install --upgrade pip
pip install -r requirements.txt

# Diagnostic step: Check Django settings, INSTALLED_APPS, and available commands
echo "=== Checking Django settings and INSTALLED_APPS ==="
python manage.py shell --settings=projectmanagement.settings.production -c "from django.conf import settings; print(f'DEBUG: {settings.DEBUG}'); print(f'INSTALLED_APPS: {settings.INSTALLED_APPS}'); from django.core.management import get_commands; print(f'Available commands: {list(get_commands().keys())}')"

# Set up static files
echo -e "\n=== Collecting static files ==="
python manage.py collectstatic --settings=projectmanagement.settings.production --noinput --clear

# Run database migrations
echo -e "\n=== Running database migrations ==="
python manage.py migrate --settings=projectmanagement.settings.production --noinput

# Create cache table if using database cache
echo -e "\n=== Setting up cache table ==="
python manage.py createcachetable --settings=projectmanagement.settings.production

echo -e "\n✅ Build completed successfully!"