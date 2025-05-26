#!/usr/bin/env python
"""
Test script to check profile endpoint functionality
"""
import os
import sys
import django
import requests
import json

# Add the project directory to the Python path
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')

# Setup Django
django.setup()

from users.models import User

def create_test_user():
    """Create a test user if it doesn't exist"""
    username = "testuser"
    email = "test@example.com"
    password = "testpass123"
    
    # Check if user already exists and delete it to start fresh
    try:
        existing_user = User.objects.get(email=email)
        existing_user.delete()
        print(f"Deleted existing test user with email: {email}")
    except User.DoesNotExist:
        pass
    
    try:
        existing_user = User.objects.get(username=username)
        existing_user.delete()
        print(f"Deleted existing test user with username: {username}")
    except User.DoesNotExist:
        pass
    
    # Create fresh user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name='Test',
        last_name='User',
        phone_number='+1234567890',
        job_title='Software Developer',
        bio='Test user bio'
    )
    print(f"Created fresh test user: {username} with email: {email}")
    
    return email, password  # Return email since that's what we use for auth

def get_auth_token(email, password):
    """Get JWT token for authentication"""
    url = "http://127.0.0.1:8000/api/v1/auth/jwt/create/"
    data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        tokens = response.json()
        return tokens['access']
    else:
        print(f"Failed to get token: {response.status_code}")
        print(response.text)
        return None

def test_profile_endpoint(token):
    """Test the profile endpoint"""
    url = "http://127.0.0.1:8000/api/v1/users/me/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test GET request
    print("\n=== Testing GET /api/v1/users/me/ ===")
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Response data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

def test_profile_update(token):
    """Test profile update"""
    url = "http://127.0.0.1:8000/api/v1/users/me/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test PATCH request
    print("\n=== Testing PATCH /api/v1/users/me/ ===")
    update_data = {
        "first_name": "Updated",
        "last_name": "User",
        "bio": "Updated bio from test script"
    }
    
    response = requests.patch(url, json=update_data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Updated data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("=== Profile Endpoint Test ===")
    
    # Create test user
    email, password = create_test_user()
    
    # Get auth token
    print(f"\nGetting auth token for {email}...")
    token = get_auth_token(email, password)
    
    if not token:
        print("Failed to get authentication token. Exiting.")
        sys.exit(1)
    
    print(f"Got token: {token[:20]}...")
    
    # Test profile endpoint
    if test_profile_endpoint(token):
        test_profile_update(token)
    
    print("\n=== Test Complete ===")
