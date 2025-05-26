#!/usr/bin/env python3
import requests
import json

# Configuration
BASE_URL = 'http://localhost:8000'
USERNAME = 'lakshay@example.com'  # Most Django apps use email for login
PASSWORD = 'password123'  # Guessing a common test password
PROJECT_ID = '93056c8a-c381-4da3-9eb5-471c917b8e83'

def get_auth_token():
    """Get authentication token"""
    login_url = f"{BASE_URL}/api/v1/auth/jwt/create/"
    response = requests.post(login_url, json={
        'email': USERNAME,  # Django uses email for login, not username
        'password': PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get('access')
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_endpoints():
    """Test various endpoints"""
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("=== TESTING ENDPOINTS ===")
    
    # Test 1: Project members endpoint (403 issue)
    print("\n1. Testing project members endpoint...")
    members_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/members/"
    response = requests.get(members_url, headers=headers)
    print(f"   GET {members_url}")
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        print(f"   Success: Found {len(response.json())} members")
    
    # Test 2: Activity logs endpoint (500 issue - should be fixed)
    print("\n2. Testing activity logs endpoint...")
    activity_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/activity_logs/"
    response = requests.get(activity_url, headers=headers)
    print(f"   GET {activity_url}")
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    else:
        print(f"   Success: Found {len(response.json())} activity logs")
    
    # Test 3: Add member endpoint (400 issue)
    print("\n3. Testing add member endpoint...")
    add_member_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/add_member/"
    test_user_data = {
        'user': 2,  # Assuming there's a user with ID 2
        'role': 'member'
    }
    response = requests.post(add_member_url, headers=headers, json=test_user_data)
    print(f"   POST {add_member_url}")
    print(f"   Data: {test_user_data}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    # Test 4: Tasks endpoint (frontend issue)
    print("\n4. Testing tasks endpoint...")
    tasks_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/tasks/"
    response = requests.get(tasks_url, headers=headers)
    print(f"   GET {tasks_url}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response type: {type(data)}")
        if isinstance(data, list):
            print(f"   Success: Array with {len(data)} tasks")
        else:
            print(f"   Warning: Response is not an array: {data}")
    else:
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_endpoints()
