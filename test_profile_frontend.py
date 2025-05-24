#!/usr/bin/env python3
"""
Test script to verify the profile frontend page functionality.
This script will:
1. Test the profile page requires authentication
2. Login with test credentials
3. Check if profile data loads correctly on the frontend
4. Test profile update functionality through the frontend
"""

import requests
import json
import os
import sys

# Add the Django project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

BASE_URL = 'http://127.0.0.1:8000'

def get_csrf_token(session):
    """Get CSRF token from the server"""
    response = session.get(f'{BASE_URL}/')
    csrf_token = None
    if 'csrftoken' in session.cookies:
        csrf_token = session.cookies['csrftoken']
    return csrf_token

def create_test_user():
    """Create or get a test user"""
    email = 'test@example.com'
    
    # Delete existing user if exists
    User.objects.filter(email=email).delete()
    
    # Create test user
    user = User.objects.create_user(
        username='testuser',
        email=email,
        password='testpass123',
        first_name='Test',
        last_name='User',
        phone_number='+1234567890',
        job_title='Software Developer',
        bio='Test user bio'
    )
    print(f"Created test user: {user.username} with email: {user.email}")
    return user

def get_jwt_token(email, password):
    """Get JWT token for authentication"""
    response = requests.post(f'{BASE_URL}/api/v1/auth/jwt/create/', {
        'email': email,
        'password': password
    })
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access')
        print(f"Got JWT token for {email}")
        return access_token
    else:
        print(f"Failed to get token: {response.status_code} - {response.text}")
        return None

def test_profile_page_authentication():
    """Test if profile page requires authentication"""
    print("\n=== Testing Profile Page Authentication ===")
    
    # Test without authentication
    response = requests.get(f'{BASE_URL}/profile/')
    print(f"Profile page without auth - Status: {response.status_code}")
    
    if response.status_code == 200:
        # Check if the response contains any user data or redirects to login
        if 'login' in response.text.lower() or 'unauthorized' in response.text.lower():
            print("✅ Profile page properly handles unauthenticated access")
        else:
            # Check if template variables are empty
            if '{{ user.first_name }}' in response.text or response.text.count('{{') > 0:
                print("❌ Profile page template variables not rendered properly")
            else:
                print("⚠️  Profile page accessible without auth but template rendered")
    
    return response

def test_profile_page_with_auth():
    """Test profile page with proper authentication"""
    print("\n=== Testing Profile Page with Authentication ===")
    
    # Create test user and get token
    user = create_test_user()
    token = get_jwt_token(user.email, 'testpass123')
    
    if not token:
        print("❌ Failed to get authentication token")
        return None
    
    # Test with authentication
    session = requests.Session()
    
    # Set JWT token in cookies (the way the frontend handles it)
    session.cookies.set('access_token', token, domain='127.0.0.1')
    
    # Get CSRF token
    csrf_token = get_csrf_token(session)
    
    # Access profile page with authentication
    response = session.get(f'{BASE_URL}/profile/')
    print(f"Profile page with auth - Status: {response.status_code}")
    
    if response.status_code == 200:
        # Check if user data is properly loaded in the HTML
        if user.first_name in response.text and user.email in response.text:
            print("✅ Profile page loads user data correctly")
        else:
            print("❌ Profile page does not show user data")
            print("Looking for:", user.first_name, user.email)
            if "{{ user." in response.text:
                print("⚠️  Template variables not rendered - context issue")
    
    return session, user, csrf_token

def test_profile_api_integration():
    """Test the profile page's integration with the API"""
    print("\n=== Testing Profile API Integration ===")
    
    session, user, csrf_token = test_profile_page_with_auth()
    if not session:
        return
    
    # Test if the profile page can call the API
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json',
    }
    
    # Test the API endpoint that the frontend uses
    response = session.get(f'{BASE_URL}/api/v1/users/me/', headers=headers)
    print(f"API /users/me/ call - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Profile API accessible from authenticated session")
        print(f"API returned: {data.get('first_name')} {data.get('last_name')}")
    else:
        print(f"❌ Profile API call failed: {response.text}")
    
    # Test profile update via API
    update_data = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'bio': 'Updated bio via test'
    }
    
    response = session.patch(f'{BASE_URL}/api/v1/users/me/', 
                           data=json.dumps(update_data), 
                           headers=headers)
    print(f"API profile update - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Profile update via API successful")
        updated_data = response.json()
        print(f"Updated to: {updated_data.get('first_name')} {updated_data.get('last_name')}")
    else:
        print(f"❌ Profile update failed: {response.text}")

def main():
    print("=== Profile Frontend Test ===")
    
    # Test 1: Authentication requirement
    test_profile_page_authentication()
    
    # Test 2: Authentication with proper credentials
    test_profile_page_with_auth()
    
    # Test 3: API integration
    test_profile_api_integration()
    
    print("\n=== Test Complete ===")

if __name__ == '__main__':
    main()
