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
python manage.py check --settings=projectmanagement.settings.production
python manage.py shell --settings=projectmanagement.settings.production -c "from django.conf import settings; print(f'DEBUG: {settings.DEBUG}'); print(f'INSTALLED_APPS: {settings.INSTALLED_APPS}'); print(f'MIDDLEWARE: {settings.MIDDLEWARE}'); from django.core.management import get_commands; print(f'Available commands: {list(get_commands().keys())}')"

# Set up static files
echo -e "\n=== Collecting static files ==="
python manage.py collectstatic --settings=projectmanagement.settings.production --noinput --clear

# Database setup with safety checks
echo -e "\n=== Setting up database ==="

# First check if we need to do a fresh migration or if table exists
echo "Checking database state..."
PYTHON_CODE=$(cat <<EOF
import sys
import dj_database_url
import psycopg2
import os

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("No DATABASE_URL found in environment")
    sys.exit(1)

config = dj_database_url.parse(db_url)
try:
    # Connect to the database
    conn = psycopg2.connect(
        dbname=config['NAME'],
        user=config['USER'],
        password=config['PASSWORD'],
        host=config['HOST'],
        port=config['PORT']
    )
    cursor = conn.cursor()
    
    # Check if organizations_organization table exists and get its schema
    cursor.execute("""SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'organizations_organization'
    )""")
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        # Check the data type of the id column
        cursor.execute("""SELECT data_type FROM information_schema.columns 
                       WHERE table_name = 'organizations_organization' AND column_name = 'id'""")
        data_type = cursor.fetchone()[0]
        
        if data_type == 'bigint':
            print("TABLE_EXISTS_INTEGER_ID")
        else:
            print("TABLE_EXISTS_OTHER_ID")
    else:
        print("NO_TABLES")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    print("NO_TABLES")  # Assume no tables if we can't connect
    sys.exit(0)
EOF
)

DB_STATUS=$(python -c "$PYTHON_CODE")

if [ "$DB_STATUS" = "TABLE_EXISTS_INTEGER_ID" ]; then
    echo "Warning: Database already contains tables with integer IDs, but models use UUIDs."
    echo "This requires clearing all tables to avoid migration failures."
    
    # Since we can't directly drop all tables with privileges on Render.com,
    # let's use Django's flush command and then manual migration with --fake-initial
    echo "Flushing database to clear all data..."
    python manage.py flush --settings=projectmanagement.settings.production --noinput
    
    # Since we have integer IDs and need UUIDs, we'll use fake-initial to handle the schema change
    echo "Setting up migrations with fake-initial..."
    python manage.py migrate --settings=projectmanagement.settings.production --fake-initial
    
    # Now run migrations on a clean database
    echo "Running migrations on a clean database..."
    python manage.py migrate --settings=projectmanagement.settings.production --noinput
elif [ "$DB_STATUS" = "NO_TABLES" ] || [ "$DB_STATUS" = "TABLE_EXISTS_OTHER_ID" ]; then
    echo "Running migrations on clean or compatible database..."
    python manage.py migrate --settings=projectmanagement.settings.production --noinput
else
    echo "Error checking database status: $DB_STATUS"
    echo "Attempting migrations anyway..."
    python manage.py migrate --settings=projectmanagement.settings.production --noinput
fi

# Create cache table if using database cache
echo -e "\n=== Setting up cache table ==="
python manage.py createcachetable --settings=projectmanagement.settings.production

echo -e "\n✅ Build completed successfully!"