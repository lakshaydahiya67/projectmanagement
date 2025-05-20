#!/bin/bash

# Error handling
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default environment variables
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-"projectmanagement.settings"}

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory if not already there
if [ "$PWD" != "$SCRIPT_DIR" ]; then
    cd "$SCRIPT_DIR"
    echo -e "${YELLOW}Changed directory to $SCRIPT_DIR${NC}"
fi

# Function to set up environment
setup_environment() {
    echo -e "${GREEN}Setting up environment...${NC}"
    
    # Check if .env file exists and create it if it doesn't
    if [ ! -f .env ]; then
        echo -e "${YELLOW}No .env file found. Creating from env-example...${NC}"
        if [ -f env-example ]; then
            cp env-example .env
            echo -e "${GREEN}.env file created successfully.${NC}"
        else
            echo -e "${RED}env-example file not found. Please create .env manually.${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}.env file found.${NC}"
    fi
    
    # Source the .env file if it exists
    if [ -f .env ]; then
        echo -e "${GREEN}Loading environment variables...${NC}"
        export $(grep -v '^#' .env | xargs)
    fi
    
    return 0
}

# Function to install dependencies
install_dependencies() {
    echo -e "${GREEN}Installing Python dependencies...${NC}"
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
    # Check if we need to install additional packages
    if [ "$1" = "dev" ]; then
        echo -e "${GREEN}Installing development dependencies...${NC}"
        pip install gunicorn
    fi
    
    if [ "$1" = "render" ]; then
        echo -e "${GREEN}Installing production dependencies...${NC}"
        pip install gunicorn
    fi
}

# Function to check Django settings
check_django_settings() {
    echo -e "${GREEN}Checking Django settings and INSTALLED_APPS...${NC}"
    python manage.py check
    python manage.py shell -c "from django.conf import settings; print(f'DEBUG: {settings.DEBUG}'); print(f'INSTALLED_APPS: {settings.INSTALLED_APPS}'); print(f'MIDDLEWARE: {settings.MIDDLEWARE}'); from django.core.management import get_commands; print(f'Available commands: {list(get_commands().keys())}')"
}

# Function to set up the database
setup_database() {
    echo -e "${GREEN}Setting up database...${NC}"
    
    # Ensure database directory exists if using SQLite
    if [ -n "$DATABASE_PATH" ]; then
        echo -e "${GREEN}Ensuring database directory exists: $DATABASE_PATH${NC}"
        mkdir -p $(dirname "$DATABASE_PATH")
        touch "$DATABASE_PATH"
    fi
    
    # Make migrations for each app
    if [ "$1" = "dev" ]; then
        echo -e "${GREEN}Making migrations for each app...${NC}"
        python manage.py makemigrations users
        python manage.py makemigrations organizations
        python manage.py makemigrations projects
        python manage.py makemigrations tasks
        python manage.py makemigrations notifications
        python manage.py makemigrations analytics
        python manage.py makemigrations activitylogs
    fi
    
    # Apply migrations
    echo -e "${GREEN}Applying migrations...${NC}"
    python manage.py migrate --noinput
    
    # Create cache table if using database cache
    echo -e "${GREEN}Setting up cache table...${NC}"
    python manage.py createcachetable
}

# Function to collect static files
collect_static_files() {
    echo -e "${GREEN}Collecting static files...${NC}"
    
    # Check if we're in Docker environment
    if [ "$1" = "docker" ]; then
        # Create staticfiles directory
        mkdir -p /app/staticfiles
        chmod -R 777 /app/staticfiles
        
        # Run collectstatic
        python manage.py collectstatic --noinput
        
        # Set correct permissions
        chmod -R 755 /app/staticfiles
    elif [ "$1" = "staticfiles" ]; then
        # For manual staticfiles management with Docker
        docker exec -u root django mkdir -p /app/staticfiles
        docker exec -u root django chmod -R 777 /app/staticfiles
        docker exec -u root django python manage.py collectstatic --noinput
        docker exec -u root django chmod -R 755 /app/staticfiles
    else
        # For local development or Render deployment
        python manage.py collectstatic --noinput --clear
    fi
}

# Function to create superuser
create_superuser() {
    echo -e "${GREEN}Checking if superuser needs to be created...${NC}"
    
    # Variables for superuser creation
    local username=${DJANGO_SUPERUSER_USERNAME:-admin}
    local email=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
    local password=${DJANGO_SUPERUSER_PASSWORD:-adminpassword}
    local first_name=${DJANGO_SUPERUSER_FIRST_NAME:-Admin}
    local last_name=${DJANGO_SUPERUSER_LAST_NAME:-User}
    
    # Only proceed if the environment variables are set
    if [ -n "$username" ] && [ -n "$email" ] && [ -n "$password" ]; then
        python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '$DJANGO_SETTINGS_MODULE')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    try:
        User.objects.create_superuser(
            username='$username',
            email='$email',
            password='$password', 
            first_name='$first_name', 
            last_name='$last_name'
        )
        print('Superuser created successfully.')
    except Exception as e:
        print(f'Error creating superuser: {e}')
        # Try alternative method if the first fails
        try:
            User.objects.create_superuser(
                email='$email',
                password='$password'
            )
            print('Superuser created with alternative method.')
        except Exception as e:
            print(f'Alternative method also failed: {e}')
else:
    print('Superuser already exists.')
"
    else
        echo -e "${YELLOW}Skipping superuser creation (environment variables not set)${NC}"
    fi
}

# Function to test email configuration
test_email_configuration() {
    if [ "$EMAIL_BACKEND" = "django.core.mail.backends.smtp.EmailBackend" ]; then
        echo -e "${GREEN}Testing email configuration...${NC}"
        python -m email_test admin@example.com || {
            echo -e "${YELLOW}Warning: Email configuration test failed but continuing startup${NC}"
        }
    fi
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local timeout=${3:-60}
    
    echo -e "${GREEN}Waiting for $host:$port to be available...${NC}"
    ./docker/wait-for-it.sh $host:$port -t $timeout
}

# Main function
main() {
    local mode=$1
    shift  # Remove the first argument
    
    case $mode in
        # Build mode for Render deployment
        "build" | "render")
            setup_environment
            install_dependencies "render"
            check_django_settings
            collect_static_files "render"
            setup_database "render"
            create_superuser
            echo -e "${GREEN}✅ Build completed successfully!${NC}"
            ;;
        
        # Docker mode for container initialization
        "docker" | "django")
            wait_for_service ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}
            test_email_configuration
            setup_database "docker"
            collect_static_files "docker"
            create_superuser
            echo -e "${GREEN}Starting Django application...${NC}"
            if [ "$mode" = "django" ]; then
                exec gunicorn projectmanagement.wsgi:application --bind 0.0.0.0:${PORT:-8000}
            fi
            ;;
        
        # Celery worker mode
        "celery")
            wait_for_service ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}
            wait_for_service django 8000
            echo -e "${GREEN}Starting Celery worker...${NC}"
            exec celery -A projectmanagement worker \
              --concurrency=4 \
              --max-tasks-per-child=10 \
              --max-memory-per-child=256000 \
              --loglevel=info
            ;;
        
        # Celery beat mode
        "celerybeat")
            wait_for_service ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}
            wait_for_service django 8000
            echo -e "${GREEN}Starting Celery beat...${NC}"
            exec celery -A projectmanagement beat --loglevel=info
            ;;
        
        # Development mode
        "dev")
            setup_environment
            collect_static_files "dev"
            setup_database "dev"
            create_superuser
            echo -e "${GREEN}Starting development server...${NC}"
            python manage.py runserver 0.0.0.0:8000
            ;;
        
        # Static files management
        "staticfiles")
            collect_static_files "staticfiles"
            echo -e "${GREEN}Done! Static files should now be properly accessible.${NC}"
            ;;
        
        # Environment setup only
        "env")
            setup_environment
            echo -e "${GREEN}Environment setup complete!${NC}"
            echo ""
            echo -e "${YELLOW}You may want to edit the .env file with your specific configuration.${NC}"
            echo ""
            echo -e "${YELLOW}For more information on available settings, see ENV_DOCS.md${NC}"
            ;;
        
        # Help/usage
        *)
            echo -e "${GREEN}Usage: $0 <mode> [options]${NC}"
            echo ""
            echo "Modes:"
            echo "  build, render   - Build for Render.com deployment"
            echo "  docker, django  - Initialize and start Django in Docker"
            echo "  celery          - Start Celery worker"
            echo "  celerybeat      - Start Celery beat scheduler"
            echo "  dev             - Run in development mode"
            echo "  staticfiles     - Collect and manage static files"
            echo "  env             - Setup environment only"
            echo ""
            echo "Examples:"
            echo "  $0 build        - Build for deployment"
            echo "  $0 dev          - Run in development mode"
            echo "  $0 staticfiles  - Collect static files"
            ;;
    esac
}

# Run the main function with all arguments
main "$@" 