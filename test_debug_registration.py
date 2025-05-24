#!/usr/bin/env python3
"""
Test script to trigger registration API and check debug logs
"""

import requests
import json
import time

def test_registration_with_debug():
    """Test registration and observe debug logs in server output"""
    
    base_url = "http://localhost:8001"
    
    # Registration data
    registration_data = {
        "username": f"debugtest_{int(time.time())}",
        "email": f"debugtest_{int(time.time())}@example.com",
        "password": "testpassword123",
        "re_password": "testpassword123",
        "first_name": "DEBUG",
        "last_name": "TEST"
    }
    
    print("=== Testing Registration with Debug Logging ===")
    print(f"Sending registration data: {json.dumps(registration_data, indent=2)}")
    print("\nSending POST request to /api/v1/auth/users/...")
    
    try:
        # Make registration request
        response = requests.post(
            f"{base_url}/api/v1/auth/users/",
            json=registration_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("\n✅ Registration successful!")
            print("🔍 Check the server terminal for debug logs...")
            print("   - Look for 'DEBUG: UserCreateSerializer.validate called'")
            print("   - Look for 'DEBUG: UserCreateSerializer.create called'")
        else:
            print(f"\n❌ Registration failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_registration_with_debug()
