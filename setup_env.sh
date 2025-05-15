#!/bin/bash

# Setup environment variables script for projectmanagement

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

echo -e "${GREEN}Setting up environment variables for Project Management App${NC}"

# Check if .env already exists
if [ -f .env ]; then
    echo -e "${YELLOW}A .env file already exists. Do you want to overwrite it? (y/n)${NC}"
    read -r answer
    if [ "$answer" != "y" ]; then
        echo "Keeping existing .env file."
        exit 0
    fi
fi

# Copy example file if it exists
if [ -f abc.txt ]; then
    cp abc.txt .env
    echo -e "${GREEN}Created .env file from abc.txt${NC}"
else
    # Create .env file with default values
    cat > .env << EOL
# Django Project Environment Variables
# See ENV_DOCS.md for detailed descriptions of each variable

# Core Django Settings
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
ALLOWED_HOSTS=localhost,127.0.0.1

# Frontend URL Configuration
FRONTEND_URL=http://localhost:3000

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_ALL_ORIGINS=True

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=

# JWT Settings
JWT_SIGNING_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Redis Settings (for WebSockets and Celery)
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Celery Settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Default Page Size for API Pagination
DEFAULT_PAGE_SIZE=10
EOL
    echo -e "${GREEN}Created new .env file with default values${NC}"
fi

# Setup frontend environment
if [ ! -d "$SCRIPT_DIR/frontend" ]; then
    echo -e "${YELLOW}Frontend directory not found, skipping frontend environment setup${NC}"
else
    cd "$SCRIPT_DIR/frontend" || exit

    if [ -f .env ]; then
        echo -e "${YELLOW}A frontend .env file already exists. Do you want to overwrite it? (y/n)${NC}"
        read -r answer
        if [ "$answer" != "y" ]; then
            echo "Keeping existing frontend .env file."
            cd "$SCRIPT_DIR"
            exit 0
        fi
    fi

    # Check if frontend abc.txt exists
    if [ -f abc.txt ]; then
        cp abc.txt .env
        echo -e "${GREEN}Created frontend .env file from abc.txt${NC}"
    else
        # Create frontend .env file
        cat > .env << EOL
# React Frontend Environment Variables

# API URL Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WEBSOCKET_URL=ws://localhost:8000/ws

# Authentication Settings
REACT_APP_TOKEN_EXPIRY_THRESHOLD_MINS=5

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_NOTIFICATIONS=true

# UI Settings
REACT_APP_DEFAULT_THEME=light
REACT_APP_ITEMS_PER_PAGE=10
EOL
        echo -e "${GREEN}Created frontend .env file${NC}"
    fi
    cd "$SCRIPT_DIR"
fi

echo -e "${GREEN}Environment setup complete!${NC}"
echo -e "${YELLOW}Remember to review and update the .env files with your specific values.${NC}" 