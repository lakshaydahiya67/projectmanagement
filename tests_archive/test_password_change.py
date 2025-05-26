#!/usr/bin/env python3
"""
Test script for password change functionality
"""

import requests
import json
import os
import sys

# Add the project directory to Python path
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')

import django
django.setup()

from django.contrib.auth import get_user_model

BASE_URL = 'http://127.0.0.1:8000'
API_BASE_URL = f'{BASE_URL}/api/v1'

def test_password_change():
    """Test password change functionality"""
    print("🔐 Testing Password Change Functionality")
    print("=" * 50)
    
    # Test credentials
    email = 'testuser@example.com'
    old_password = 'OldPassword123!'
    new_password = 'NewPassword456!'
    
    # Create test user if not exists
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
        # Reset password to known state
        user.set_password(old_password)
        user.save()
        print(f"✅ Using existing test user: {email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=email,  # Use email as username since USERNAME_FIELD is email
            email=email,
            password=old_password,
            first_name='Test',
            last_name='User'
        )
        print(f"✅ Created test user: {email}")
    
    # Step 1: Login to get JWT token
    print("\n1. Logging in...")
    login_response = requests.post(f'{API_BASE_URL}/auth/jwt/create/', {
        'email': email,
        'password': old_password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    tokens = login_response.json()
    access_token = tokens['access']
    print(f"✅ Login successful, got access token")
    
    # Step 2: Test password change
    print("\n2. Testing password change...")
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    change_password_data = {
        'old_password': old_password,
        'new_password': new_password,
        'confirm_password': new_password
    }
    
    change_response = requests.post(
        f'{API_BASE_URL}/users/{user.id}/change_password/',
        headers=headers,
        json=change_password_data
    )
    
    print(f"User ID: {user.id}")
    print(f"Change password URL: {API_BASE_URL}/users/{user.id}/change_password/")
    print(f"Password change response status: {change_response.status_code}")
    print(f"Password change response: {change_response.text}")
    
    if change_response.status_code == 200:
        print("✅ Password change successful!")
        
        # Step 3: Test login with new password
        print("\n3. Testing login with new password...")
        new_login_response = requests.post(f'{API_BASE_URL}/auth/jwt/create/', {
            'email': email,
            'password': new_password
        })
        
        if new_login_response.status_code == 200:
            print("✅ Login with new password successful!")
            
            # Step 4: Test that old password no longer works
            print("\n4. Verifying old password no longer works...")
            old_login_response = requests.post(f'{API_BASE_URL}/auth/jwt/create/', {
                'email': email,
                'password': old_password
            })
            
            if old_login_response.status_code == 401:
                print("✅ Old password correctly rejected!")
                return True
            else:
                print(f"❌ Old password still works: {old_login_response.status_code}")
                return False
        else:
            print(f"❌ Login with new password failed: {new_login_response.status_code}")
            print(f"Response: {new_login_response.text}")
            return False
    else:
        print(f"❌ Password change failed: {change_response.status_code}")
        print(f"Response: {change_response.text}")
        return False

def test_password_change_validation():
    """Test password change validation"""
    print("\n\n🔍 Testing Password Change Validation")
    print("=" * 50)
    
    # Test credentials
    email = 'testuser@example.com'
    password = 'TestPassword123!'
    
    # Get or create test user
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=email,  # Use email as username since USERNAME_FIELD is email
            email=email,
            password=password,
            first_name='Test',
            last_name='User'
        )
    
    # Login to get token
    login_response = requests.post(f'{API_BASE_URL}/auth/jwt/create/', {
        'email': email,
        'password': password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    tokens = login_response.json()
    access_token = tokens['access']
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    test_cases = [
        {
            'name': 'Wrong old password',
            'data': {
                'old_password': 'WrongPassword123!',
                'new_password': 'NewPassword456!',
                'confirm_password': 'NewPassword456!'
            },
            'expected_status': 400
        },
        {
            'name': 'Passwords don\'t match',
            'data': {
                'old_password': password,
                'new_password': 'NewPassword456!',
                'confirm_password': 'DifferentPassword456!'
            },
            'expected_status': 400
        },
        {
            'name': 'Weak new password',
            'data': {
                'old_password': password,
                'new_password': 'weak',
                'confirm_password': 'weak'
            },
            'expected_status': 400
        },
        {
            'name': 'Missing old password',
            'data': {
                'new_password': 'NewPassword456!',
                'confirm_password': 'NewPassword456!'
            },
            'expected_status': 400
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        response = requests.post(
            f'{API_BASE_URL}/users/{user.id}/change_password/',
            headers=headers,
            json=test_case['data']
        )
        
        if response.status_code == test_case['expected_status']:
            print(f"✅ {test_case['name']} - Correctly returned {response.status_code}")
        else:
            print(f"❌ {test_case['name']} - Expected {test_case['expected_status']}, got {response.status_code}")
            print(f"Response: {response.text}")
    
    return True

if __name__ == '__main__':
    print("🧪 Starting Password Change Tests")
    print("=" * 60)
    
    try:
        # Test basic functionality
        success1 = test_password_change()
        
        # Test validation
        success2 = test_password_change_validation()
        
        if success1 and success2:
            print("\n🎉 All password change tests passed!")
        else:
            print("\n❌ Some password change tests failed!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
