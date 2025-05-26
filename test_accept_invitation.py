#!/usr/bin/env python3
import requests
import json
import sys
import random

# Configuration
BASE_URL = 'http://127.0.0.1:8000'
TEST_EMAIL = f"testuser{random.randint(1000, 9999)}@example.com"
TEST_PASSWORD = "password123"
ORGANIZATION_ID = '392eddf8-023f-4d9f-a882-d3ea18537ad0'
TOKEN = '-QV-KSjZxDWmDgC8l8bNnnB63yGI5_ud_ZAvsOrjnBA'  # Token from the invitation

def create_test_user():
    """Create a test user to accept the invitation"""
    register_url = f"{BASE_URL}/api/v1/auth/users/"
    try:
        username = f"testuser{random.randint(1000, 9999)}"
        secure_password = f"TestPassword{random.randint(1000, 9999)}@#$"
        
        user_data = {
            'email': TEST_EMAIL,
            'username': username,
            'password': secure_password,
            're_password': secure_password,
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        # Update the global test password so we can log in with it
        global TEST_PASSWORD
        TEST_PASSWORD = secure_password
        
        print(f"\nCreating test user: {TEST_EMAIL}")
        response = requests.post(register_url, json=user_data)
        
        if response.status_code == 201:
            print("User created successfully!")
            
            # Activate the user directly via Django shell (since we can't easily handle email verification)
            import django
            import os
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectmanagement.settings")
            django.setup()
            from users.models import User
            user = User.objects.get(email=TEST_EMAIL)
            user.is_active = True
            user.save()
            print("User activated successfully!")
            return True
        else:
            print(f"User creation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error during user creation: {str(e)}")
        return False

def get_auth_token(email, password):
    """Get authentication token"""
    login_url = f"{BASE_URL}/api/v1/auth/jwt/create/"
    try:
        response = requests.post(login_url, json={
            'email': email,
            'password': password
        })
        
        if response.status_code == 200:
            return response.json().get('access')
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
    
    return None

def test_accept_invitation():
    """Test accepting an invitation"""
    # Create a test user who will accept the invitation
    if not create_test_user():
        print("Failed to create test user, cannot proceed")
        return
        
    # Get auth token for the test user
    token = get_auth_token(TEST_EMAIL, TEST_PASSWORD)
    if not token:
        print("Authentication failed, cannot proceed")
        return

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Test the invitation acceptance endpoint using the correct URL pattern from the server routes
    # We're supposed to use /organizations/{org_id}/accept/{token}/
    accept_url = f"{BASE_URL}/organizations/{ORGANIZATION_ID}/accept/{TOKEN}/"
    
    print(f"\nTesting invitation acceptance with URL: {accept_url}")
    response = requests.post(accept_url, headers=headers)
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("Invitation accepted successfully!")
    else:
        print(f"Failed to accept invitation: {response.text}")
    
    # Check the HTML version of the invitation acceptance page
    web_url = f"{BASE_URL}/organizations/{ORGANIZATION_ID}/accept/{TOKEN}/"
    print(f"\nChecking web acceptance URL: {web_url}")
    response = requests.get(web_url, headers=headers)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print("Web acceptance page loaded successfully")
    else:
        print(f"Failed to load web acceptance page: {response.status_code}")

if __name__ == "__main__":
    test_accept_invitation()
