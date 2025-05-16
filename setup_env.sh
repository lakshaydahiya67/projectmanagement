#!/bin/bash

# Exit script if any command fails
set -e

echo "Setting up environment files for Project Management application..."

# Backend .env setup
if [ -f ".env" ]; then
    echo "Backend .env file already exists. Skipping..."
else
    echo "Creating backend .env file from env-example..."
    cp env-example .env
    echo "Backend .env file created successfully."
fi

# Frontend .env setup
if [ -f "frontend/.env" ]; then
    echo "Frontend .env file already exists. Skipping..."
else
    echo "Creating frontend .env file from .env-example..."
    cp frontend/.env-example frontend/.env
    echo "Frontend .env file created successfully."
fi

echo "Environment setup complete!"
echo ""
echo "You may want to edit the .env files with your specific configuration:"
echo "  - Backend: .env"
echo "  - Frontend: frontend/.env"
echo ""
echo "For more information on available settings, see ENV_DOCS.md" 