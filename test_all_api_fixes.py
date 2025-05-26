#!/usr/bin/env python3
import requests
import json

# Configuration
BASE_URL = 'http://localhost:8080'
USERNAME = 'admin@example.com'  # Use our newly created superuser
PASSWORD = 'admin'  # Password for superuser
PROJECT_ID = '93056c8a-c381-4da3-9eb5-471c917b8e83'

def get_auth_token():
    """Get authentication token"""
    login_url = f"{BASE_URL}/api/v1/auth/jwt/create/"
    try:
        response = requests.post(login_url, json={
            'email': USERNAME,
            'password': PASSWORD
        })
        
        if response.status_code == 200:
            return response.json().get('access')
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            
            # Try alternative username format if email login fails
            alt_response = requests.post(login_url, json={
                'username': 'lakshay',
                'password': PASSWORD
            })
            if alt_response.status_code == 200:
                return alt_response.json().get('access')
            else:
                print(f"Alternative login also failed: {alt_response.status_code} - {alt_response.text}")
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
    
    return None

def test_api_endpoints():
    """Test all fixed API endpoints"""
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed. Cannot proceed with testing.")
        return False
    
    print("✅ Authentication successful.")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test endpoints
    print("\n=== Testing Fixed Endpoints ===")
    
    # 1. Test members endpoint (403 Forbidden issue)
    members_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/members/"
    print(f"\n1. Testing project members endpoint: GET {members_url}")
    members_response = requests.get(members_url, headers=headers)
    print(f"   Status: {members_response.status_code}")
    if members_response.status_code == 200:
        print(f"   ✅ Members endpoint fixed!")
        print(f"   Found {len(members_response.json())} members")
    else:
        print(f"   ❌ Members endpoint still has issues: {members_response.text}")
    
    # 2. Test activity logs endpoint (500 Internal Server Error issue)
    logs_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/activity_logs/"
    print(f"\n2. Testing activity logs endpoint: GET {logs_url}")
    logs_response = requests.get(logs_url, headers=headers)
    print(f"   Status: {logs_response.status_code}")
    if logs_response.status_code == 200:
        print(f"   ✅ Activity logs endpoint fixed!")
        print(f"   Found {len(logs_response.json())} activity logs")
    else:
        print(f"   ❌ Activity logs endpoint still has issues: {logs_response.text}")
    
    # 3. Test add member endpoint (400 Bad Request issue due to unique constraint)
    add_member_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/add_member/"
    print(f"\n3. Testing add_member endpoint: POST {add_member_url}")
    
    # Testing with our admin user (who we already added to project)
    user_data = {
        'user': '5e9dbb0c-e840-425b-ac29-544e39468ae8',  # Admin user ID from previous script output
        'role': 'member'
    }
    
    add_member_response = requests.post(add_member_url, headers=headers, json=user_data)
    print(f"   Status: {add_member_response.status_code}")
    
    if add_member_response.status_code in [200, 201]:
        print(f"   ✅ Add member endpoint fixed!")
        print(f"   Response: {add_member_response.text}")
    else:
        print(f"   ❌ Add member endpoint still has issues: {add_member_response.text}")
    
    # 4. Test tasks endpoint (frontend TypeError issue with forEach)
    tasks_url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/tasks/"
    print(f"\n4. Testing tasks endpoint: GET {tasks_url}")
    tasks_response = requests.get(tasks_url, headers=headers)
    print(f"   Status: {tasks_response.status_code}")
    
    if tasks_response.status_code == 200:
        data = tasks_response.json()
        print(f"   Response type: {type(data)}")
        
        if isinstance(data, list):
            print(f"   ✅ Tasks endpoint returns an array! Frontend TypeError fixed!")
            print(f"   Found {len(data)} tasks")
        else:
            print(f"   ❌ Tasks endpoint doesn't return an array, still has issues")
    else:
        print(f"   ❌ Tasks endpoint failed with status {tasks_response.status_code}")
        print(f"   Error: {tasks_response.text}")
    
    print("\n=== Summary of API Endpoint Fixes ===")
    endpoints = {
        "Project Members": members_response.status_code == 200,
        "Activity Logs": logs_response.status_code == 200,
        "Add Member": add_member_response.status_code in [200, 201],
        "Tasks Array": tasks_response.status_code == 200 and isinstance(tasks_response.json(), list)
    }
    
    for endpoint, is_fixed in endpoints.items():
        status = "✅ FIXED" if is_fixed else "❌ STILL BROKEN"
        print(f"{endpoint}: {status}")
    
    return all(endpoints.values())

if __name__ == "__main__":
    if test_api_endpoints():
        print("\n🎉 All API endpoints have been successfully fixed!")
    else:
        print("\n⚠️ Some API endpoints still need fixing. Review the issues above.")
