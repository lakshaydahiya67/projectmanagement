#!/bin/bash

# Exit on error and print commands as they are executed
set -ex

# Install Python dependencies
echo "=== Installing Python dependencies ==="
python -m pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js dependencies and build the frontend
echo -e "\n=== Building frontend ==="
cd frontend
npm ci --prefer-offline --no-audit --progress=false
CI=false npm run build
cd ..

# Set up static files
echo -e "\n=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

# Run database migrations
echo -e "\n=== Running database migrations ==="
python manage.py migrate --noinput

# Create cache table if using database cache
echo -e "\n=== Setting up cache table ==="
python manage.py createcachetable

echo -e "\n✅ Build completed successfully!"