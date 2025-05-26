#!/usr/bin/env python3
"""
Test script to verify the authentication fix
"""
import requests
import json

def test_login():
    """Test login functionality after service worker fix"""
    print("Testing login functionality...")
    
    # Test login endpoint - this should now work without service worker interference
    login_url = "http://127.0.0.1:8001/api/v1/auth/jwt/create/"
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    print(f"Making login request to: {login_url}")
    print(f"Login data: {login_data}")
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            tokens = response.json()
            print("✅ Login successful!")
            print(f"Access token (first 50 chars): {tokens['access'][:50]}...")
            print(f"Refresh token (first 50 chars): {tokens['refresh'][:50]}...")
            return tokens['access']
        else:
            print("❌ Login failed!")
            print(f"Response text: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login request failed with exception: {e}")
        return None

def test_member_creation(access_token):
    """Test member creation with valid token"""
    if not access_token:
        print("No access token available, skipping member creation test")
        return
        
    print("\nTesting member creation...")
    
    # Use the correct project ID from earlier tests
    project_id = "550e8400-e29b-41d4-a716-446655440000"
    member_url = f"http://127.0.0.1:8000/api/v1/projects/{project_id}/members/"
    
    member_data = {
        "email": "newmember@example.com",
        "role": "member"
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"Making member creation request to: {member_url}")
    print(f"Member data: {member_data}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.post(member_url, json=member_data, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code in [200, 201]:
            print("✅ Member creation successful!")
            print(f"Response: {response.json()}")
        else:
            print("❌ Member creation failed!")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ Member creation request failed with exception: {e}")

def main():
    print("=" * 60)
    print("AUTHENTICATION FIX VERIFICATION TEST")
    print("=" * 60)
    
    # Test login
    access_token = test_login()
    
    # Test member creation if login was successful
    test_member_creation(access_token)
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    main()
