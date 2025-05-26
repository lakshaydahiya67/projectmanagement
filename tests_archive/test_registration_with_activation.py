#!/usr/bin/env python3
"""
Test script to manually activate a user and then test the profile API flow
"""
import requests
import json
import time
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.contrib.auth import get_user_model

BASE_URL = "http://localhost:8000"

def test_registration_and_profile_with_activation():
    """Test registration, manual activation, and profile retrieval"""
    
    User = get_user_model()
    
    # Test data
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "re_password": "TestPassword123!",
        "first_name": "TestFirst",
        "last_name": "TestLast"
    }
    
    print("=" * 60)
    print("TESTING REGISTRATION + MANUAL ACTIVATION + PROFILE FLOW")
    print("=" * 60)
    
    print(f"\n1. Testing registration with data:")
    print(json.dumps(test_user, indent=2))
    
    # Step 1: Register user
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/users/", json=test_user)
        print(f"\nRegistration response status: {response.status_code}")
        print(f"Registration response: {response.text}")
        
        if response.status_code != 201:
            print("❌ Registration failed!")
            return False
            
        registration_data = response.json()
        user_id = registration_data.get("id")
        
        print("✅ Registration successful!")
        print(f"User ID: {user_id}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration request failed: {e}")
        return False
    
    # Step 2: Manually activate the user (bypass email activation)
    try:
        user = User.objects.get(email=test_user["email"])
        print(f"\n2. Found user in database: {user.email}")
        print(f"User is_active before activation: {user.is_active}")
        
        if not user.is_active:
            user.is_active = True
            user.save()
            print("✅ User manually activated")
        else:
            print("✅ User was already active")
            
        # Verify the user's first_name and last_name in the database
        print(f"Database first_name: '{user.first_name}'")
        print(f"Database last_name: '{user.last_name}'")
        
        if user.first_name == test_user["first_name"] and user.last_name == test_user["last_name"]:
            print("✅ First and last names correctly stored in database!")
        else:
            print("❌ First and last names NOT correctly stored in database!")
            return False
            
    except User.DoesNotExist:
        print("❌ User not found in database!")
        return False
    except Exception as e:
        print(f"❌ Error activating user: {e}")
        return False
    
    # Step 3: Login to get access token
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/jwt/create/", json=login_data)
        print(f"\n3. Login response status: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Login failed!")
            print(f"Login response: {response.text}")
            return False
            
        token_data = response.json()
        access_token = token_data.get("access")
        
        if not access_token:
            print("❌ No access token received!")
            return False
            
        print("✅ Login successful, got access token")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return False
    
    # Step 4: Get user profile data
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/users/me/", headers=headers)
        print(f"\n4. Profile API response status: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Profile retrieval failed!")
            print(f"Profile response: {response.text}")
            return False
            
        profile_data = response.json()
        print(f"Profile data received:")
        print(json.dumps(profile_data, indent=2))
        
        # Check if first_name and last_name are present and correct
        first_name = profile_data.get("first_name")
        last_name = profile_data.get("last_name")
        
        print(f"\n5. Verification:")
        print(f"Expected first_name: '{test_user['first_name']}'")
        print(f"Received first_name: '{first_name}'")
        print(f"Expected last_name: '{test_user['last_name']}'")
        print(f"Received last_name: '{last_name}'")
        
        if first_name == test_user["first_name"] and last_name == test_user["last_name"]:
            print("✅ First name and last name are correctly returned by the API!")
            return True
        else:
            print("❌ First name and/or last name are missing or incorrect!")
            print("🔍 This indicates the issue is in the serializer or API response")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Profile request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_registration_and_profile_with_activation()
    print(f"\n{'='*60}")
    if success:
        print("🎉 ALL TESTS PASSED: The issue is NOT with registration or database storage!")
        print("💡 The problem must be elsewhere (frontend processing, template rendering, etc.)")
    else:
        print("❌ TESTS FAILED: There's an issue with the registration/profile API flow")
    print(f"{'='*60}")
