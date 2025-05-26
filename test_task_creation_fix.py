#!/usr/bin/env python
"""
Test the task creation endpoint to identify and fix the 404 error
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

# Test with correct port
BASE_URL = "http://localhost:8001/api/v1"

def test_task_creation_endpoint():
    """Test the task creation endpoint with correct nested URL structure"""
    
    print("=" * 70)
    print(" TESTING TASK CREATION ENDPOINT - DEBUGGING 404 ERROR")
    print("=" * 70)
    
    # Create unique identifiers
    timestamp = int(time.time())
    random_id = random.randint(1000, 9999)
    
    # First, create a user and get authentication
    user_data = {
        "username": f"test_task_create_{timestamp}_{random_id}",
        "email": f"test.task.create.{timestamp}.{random_id}@example.com", 
        "password": "TestPass123!",
        "re_password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    print(f"\n1. Creating user: {user_data['username']}")
    response = requests.post(f"{BASE_URL}/auth/users/", json=user_data)
    print(f"   User registration: {response.status_code}")
    if response.status_code != 201:
        print(f"   Registration failed: {response.text}")
        return
    
    user_id = response.json()['id']
    
    # Activate user
    user = User.objects.get(id=user_id)
    user.is_active = True
    user.save()
    print("   ✅ User activated")
    
    # Login
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/jwt/create/", json=login_data)
    print(f"   Login: {response.status_code}")
    if response.status_code != 200:
        print(f"   Login failed: {response.text}")
        return
        
    token = response.json()['access']
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ User authenticated")
    
    # Create organization
    print(f"\n2. Creating organization")
    org_data = {"name": f"Test Org {timestamp}", "description": "Test organization"}
    response = requests.post(f"{BASE_URL}/organizations/", json=org_data, headers=headers)
    print(f"   Organization: {response.status_code}")
    if response.status_code != 201:
        print(f"   Organization creation failed: {response.text}")
        return
        
    org_id = response.json()['id']
    print(f"   ✅ Organization created: {org_id}")
    
    # Create project
    print(f"\n3. Creating project")
    project_data = {
        "name": f"Test Project {timestamp}",
        "description": "Test project", 
        "organization": org_id
    }
    response = requests.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    print(f"   Project: {response.status_code}")
    if response.status_code != 201:
        print(f"   Project creation failed: {response.text}")
        return
        
    project = response.json()
    project_id = project['id']
    print(f"   ✅ Project created: {project_id}")
    
    # Create board
    print(f"\n4. Creating board")
    board_data = {"name": f"Test Board {timestamp}", "description": "Test board"}
    response = requests.post(f"{BASE_URL}/projects/{project_id}/boards/", json=board_data, headers=headers)
    print(f"   Board: {response.status_code}")
    if response.status_code != 201:
        print(f"   Board creation failed: {response.text}")
        return
        
    board = response.json()
    board_id = board['id']
    print(f"   ✅ Board created: {board_id}")
    
    # Create column
    print(f"\n5. Creating column")
    column_data = {"name": f"Test Column {timestamp}", "position": 0}
    response = requests.post(f"{BASE_URL}/projects/{project_id}/boards/{board_id}/columns/", json=column_data, headers=headers)
    print(f"   Column: {response.status_code}")
    if response.status_code != 201:
        print(f"   Column creation failed: {response.text}")
        return
        
    column = response.json()
    column_id = column['id']
    print(f"   ✅ Column created: {column_id}")
    
    print(f"\n6. Testing different task creation endpoints")
    
    task_data = {
        "title": f"Test Task {timestamp}",
        "description": "Test task description",
        "priority": "medium"
    }
    
    # Test URL patterns that might exist
    test_urls = [
        # The correct nested URL structure
        f"/projects/{project_id}/boards/{board_id}/columns/{column_id}/tasks/",
        
        # Wrong URLs that might be causing 404s
        f"/projects/{project_id}/tasks/",
        f"/projects/{project_id}/boards/{board_id}/tasks/",
        f"/tasks/",
        
        # Alternative nested structures
        f"/columns/{column_id}/tasks/",
    ]
    
    for test_url in test_urls:
        print(f"\n   Testing: POST {BASE_URL}{test_url}")
        
        # For nested routes, we don't need to include column in the data
        if 'columns/' in test_url and '/tasks/' in test_url:
            test_task_data = task_data.copy()
        else:
            # For direct routes, we need to include the column
            test_task_data = task_data.copy()
            test_task_data['column'] = column_id
            
        try:
            response = requests.post(f"{BASE_URL}{test_url}", json=test_task_data, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 201:
                print(f"   ✅ SUCCESS! Task created successfully")
                created_task = response.json()
                print(f"   Task ID: {created_task.get('id')}")
                print(f"   Task Title: {created_task.get('title')}")
                return created_task
            elif response.status_code == 404:
                print(f"   ❌ 404 Not Found - Endpoint doesn't exist")
            elif response.status_code == 405:
                print(f"   ❌ 405 Method Not Allowed")
            else:
                print(f"   ❌ Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n7. Testing with OPTIONS to see allowed methods")
    for test_url in test_urls[:2]:  # Test main ones
        try:
            response = requests.options(f"{BASE_URL}{test_url}", headers=headers)
            print(f"\n   OPTIONS {BASE_URL}{test_url}")
            print(f"   Status: {response.status_code}")
            if 'Allow' in response.headers:
                print(f"   Allowed methods: {response.headers['Allow']}")
            else:
                print(f"   No Allow header found")
        except Exception as e:
            print(f"   Exception: {e}")

if __name__ == "__main__":
    test_task_creation_endpoint()
