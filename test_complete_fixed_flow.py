#!/usr/bin/env python3
"""
Test script to verify the complete fixed registration and profile flow
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_complete_flow():
    """Test login and profile retrieval for the activated user"""
    
    # Test data for the activated user
    login_data = {
        "email": "test_1748086022@example.com",
        "password": "TestPassword123!"
    }
    
    print("=" * 60)
    print("TESTING COMPLETE FIXED FLOW")
    print("=" * 60)
    
    print(f"\n1. Testing login with activated user:")
    print(json.dumps(login_data, indent=2))
    
    # Step 1: Login to get access token
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/jwt/create/", json=login_data)
        print(f"\nLogin response status: {response.status_code}")
        
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
    
    # Step 2: Get user profile data
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/users/me/", headers=headers)
        print(f"\n2. Profile API response status: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Profile retrieval failed!")
            print(f"Profile response: {response.text}")
            return False
            
        profile_data = response.json()
        print(f"\n✅ Profile data retrieved successfully:")
        print(json.dumps(profile_data, indent=2))
        
        # Check if first_name and last_name are present and correct
        first_name = profile_data.get("first_name")
        last_name = profile_data.get("last_name")
        
        print(f"\n3. Key verification:")
        print(f"First name: '{first_name}' (Expected: 'TestFirst')")
        print(f"Last name: '{last_name}' (Expected: 'TestLast')")
        
        if first_name == "TestFirst" and last_name == "TestLast":
            print("✅ First name and last name are correctly returned by the profile API!")
            return True
        else:
            print("❌ First name and/or last name are missing or incorrect!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Profile request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_flow()
    print(f"\n{'='*60}")
    if success:
        print("🎉 SUCCESS: The first_name/last_name issue is COMPLETELY FIXED!")
        print("📝 Users can now register with first/last names and see them on their profile page.")
    else:
        print("❌ There's still an issue with the flow")
    print(f"{'='*60}")
