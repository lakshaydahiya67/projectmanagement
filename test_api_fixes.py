#!/usr/bin/env python
"""
Test script to verify API endpoint fixes
- Tests project members endpoint
- Tests add_member endpoint
- Tests activity_logs endpoint
- Tests tasks endpoint (checking array response)
"""
import requests
import json
import sys

# Configuration
BASE_URL = 'http://localhost:8000'
EMAIL = 'lakshay@example.com'  # Login with email
PASSWORD = 'password123'
PROJECT_ID = '93056c8a-c381-4da3-9eb5-471c917b8e83'  # From test data

def get_auth_token():
    """Get authentication token"""
    login_url = f"{BASE_URL}/api/v1/auth/jwt/create/"
    response = requests.post(login_url, json={
        'email': EMAIL,
        'password': PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get('access')
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_members_endpoint(token):
    """Test project members endpoint (was returning 403 Forbidden)"""
    print("\n===== Testing Project Members Endpoint =====")
    url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/members/"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        members = response.json()
        print(f"✅ Success - Found {len(members)} project members")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_add_member_endpoint(token):
    """Test add_member endpoint (was failing with unique constraint error)"""
    print("\n===== Testing Add Member Endpoint =====")
    url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/add_member/"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test with existing user (should handle idempotent requests)
    data = {
        'user': 1,  # Assuming user ID 1 exists and is already a member
        'role': 'member'
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code in (200, 201):  # 200 for existing member, 201 for new member
        print(f"✅ Success - Add member handled correctly")
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_activity_logs_endpoint(token):
    """Test activity logs endpoint (was returning 500 error)"""
    print("\n===== Testing Activity Logs Endpoint =====")
    url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/activity_logs/"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        logs = response.json()
        print(f"✅ Success - Found {len(logs)} activity logs")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_tasks_endpoint(token):
    """Test tasks endpoint (was returning object instead of array)"""
    print("\n===== Testing Tasks Endpoint =====")
    url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/tasks/"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            print(f"✅ Success - Response is an array with {len(data)} tasks")
            return True
        else:
            print(f"❌ Error: Response is not an array: {type(data)}")
            return False
    else:
        print(f"❌ Error: {response.text}")
        return False

def main():
    """Main function to run all tests"""
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token")
        sys.exit(1)
    
    results = []
    
    # Test project members endpoint
    results.append(test_members_endpoint(token))
    
    # Test add member endpoint
    results.append(test_add_member_endpoint(token))
    
    # Test activity logs endpoint (previously fixed)
    results.append(test_activity_logs_endpoint(token))
    
    # Test tasks endpoint
    results.append(test_tasks_endpoint(token))
    
    # Print summary
    print("\n===== Test Summary =====")
    total_tests = len(results)
    passed_tests = results.count(True)
    failed_tests = results.count(False)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed Tests: {passed_tests}")
    print(f"Failed Tests: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 All tests passed! All API endpoints are working correctly.")
        return 0
    else:
        print(f"\n❌ {failed_tests} tests failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
