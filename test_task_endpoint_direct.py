#!/usr/bin/env python
"""
Direct test for task creation endpoint to identify the 405 error root cause
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

import requests
import json
import time
import random
from django.contrib.auth import get_user_model
from organizations.models import Organization
from projects.models import Project, Column, Board, ProjectMember

User = get_user_model()

# Test endpoints directly
BASE_URL = "http://localhost:8000/api/v1"

def test_task_endpoint_methods():
    """Test what HTTP methods are allowed on the tasks endpoint"""
    
    print("=" * 60)
    print(" TESTING TASK ENDPOINT HTTP METHODS")
    print("=" * 60)
    
    # Create unique identifiers
    timestamp = int(time.time())
    random_id = random.randint(1000, 9999)
    
    # First, create a user and get authentication
    user_data = {
        "username": f"test_task_methods_{timestamp}_{random_id}",
        "email": f"test.task.methods.{timestamp}.{random_id}@example.com", 
        "password": "TestPass123!",
        "re_password": "TestPass123!",
        "first_name": "Test",
        "last_name": "Task"
    }
    
    # Register user
    response = requests.post(f"{BASE_URL}/auth/users/", json=user_data)
    print(f"User registration: {response.status_code}")
    if response.status_code != 201:
        print(f"Registration failed: {response.text}")
        return
    
    user_id = response.json()['id']
    
    # Activate user
    user = User.objects.get(id=user_id)
    user.is_active = True
    user.save()
    print("✅ User activated")
    
    # Login
    login_data = {
        "email": f"test.task.methods.{timestamp}.{random_id}@example.com",
        "password": "TestPass123!"
    }
    response = requests.post(f"{BASE_URL}/auth/jwt/create/", json=login_data)
    print(f"Login: {response.status_code}")
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
        
    token = response.json()['access']
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ User authenticated")
    
    # Create organization and project  
    org_data = {"name": "Test Org", "description": "Test organization"}
    response = requests.post(f"{BASE_URL}/organizations/", json=org_data, headers=headers)
    print(f"Organization creation: {response.status_code}")
    if response.status_code != 201:
        print(f"Organization creation failed: {response.text}")
        return
    org_id = response.json()['id']
    
    project_data = {
        "name": "Test Project",
        "description": "Test project",
        "organization": org_id
    }
    response = requests.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    print(f"Project creation: {response.status_code}")
    if response.status_code != 201:
        print(f"Project creation failed: {response.text}")
        return
    project = response.json()
    
    # Get the default board and column
    response = requests.get(f"{BASE_URL}/projects/{project['id']}/boards/", headers=headers)
    print(f"Get boards: {response.status_code}")
    if response.status_code != 200:
        print(f"Get boards failed: {response.text}")
        return
    boards = response.json()
    board = boards[0]
    column = board['columns'][0]
    
    print(f"✅ Setup complete. Testing task endpoint methods...")
    print(f"Board ID: {board['id']}")
    print(f"Column ID: {column['id']}")
    
    # Test different HTTP methods on /api/v1/tasks/
    methods_to_test = ['OPTIONS', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    
    for method in methods_to_test:
        print(f"\n--- Testing {method} /api/v1/tasks/ ---")
        
        try:
            if method == 'OPTIONS':
                response = requests.options(f"{BASE_URL}/tasks/", headers=headers)
            elif method == 'GET':
                response = requests.get(f"{BASE_URL}/tasks/", headers=headers)
            elif method == 'POST':
                task_data = {
                    "title": "Test Task",
                    "description": "Test task description",
                    "column": column['id']
                }
                response = requests.post(f"{BASE_URL}/tasks/", json=task_data, headers=headers)
            elif method == 'PUT':
                response = requests.put(f"{BASE_URL}/tasks/", json={}, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(f"{BASE_URL}/tasks/", json={}, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(f"{BASE_URL}/tasks/", headers=headers)
                
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            # Check allowed methods from OPTIONS response
            if method == 'OPTIONS' and 'Allow' in response.headers:
                print(f"Allowed methods: {response.headers['Allow']}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n--- Testing POST with different data ---")
    
    # Test POST with minimal data
    minimal_task_data = {"title": "Minimal Task", "column": column['id']}
    response = requests.post(f"{BASE_URL}/tasks/", json=minimal_task_data, headers=headers)
    print(f"Minimal POST Status: {response.status_code}")
    print(f"Minimal POST Response: {response.text[:200]}...")
    
    # Test POST with detailed data
    detailed_task_data = {
        "title": "Detailed Task",
        "description": "Detailed task description", 
        "column": column['id'],
        "priority": "medium",
        "due_date": "2025-06-01"
    }
    response = requests.post(f"{BASE_URL}/tasks/", json=detailed_task_data, headers=headers)
    print(f"Detailed POST Status: {response.status_code}")
    print(f"Detailed POST Response: {response.text[:200]}...")

if __name__ == "__main__":
    test_task_endpoint_methods()
