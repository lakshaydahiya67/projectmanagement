#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if .env file exists and source it
if [ ! -f .env ]; then
    echo -e "${YELLOW}No .env file found. Running setup_env.sh...${NC}"
    bash ./setup_env.sh
else
    echo -e "${GREEN}.env file found.${NC}"
fi

# Source .env file if it exists
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

echo -e "${GREEN}Collecting static files...${NC}"
python manage.py collectstatic --noinput

echo -e "${GREEN}Making migrations for each app...${NC}"
python manage.py makemigrations users
python manage.py makemigrations organizations
python manage.py makemigrations projects
python manage.py makemigrations tasks
python manage.py makemigrations notifications
python manage.py makemigrations analytics
python manage.py makemigrations activitylogs

echo -e "${GREEN}Applying migrations...${NC}"
python manage.py migrate

# Check if superuser needs to be created
echo -e "${GREEN}Checking if superuser exists...${NC}"
python -c "
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
print('Python path:', sys.path)
print('Attempting to import from .models...')

if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    # Get the model fields to determine correct parameters for create_superuser
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
        # Try alternative method if the first fails
        try:
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpassword'
            )
            print('Superuser created with alternative method.')
        except Exception as e:
            print(f'Alternative method also failed: {e}')
else:
    print('Superuser already exists.')
"

echo -e "${GREEN}Starting development server...${NC}"
python manage.py runserver 0.0.0.0:8000 