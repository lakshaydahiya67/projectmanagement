#!/bin/bash

# Exit on error and print commands as they are executed
set -ex

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js dependencies and build the frontend
echo "Building frontend..."
cd frontend
npm ci --prefer-offline --no-audit --progress=false
npm run build
cd ..

# Set up static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

echo "Build completed successfully!"