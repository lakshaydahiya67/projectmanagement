#!/bin/bash

# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies and build the frontend
cd frontend
npm install
npm run build
cd ..

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate