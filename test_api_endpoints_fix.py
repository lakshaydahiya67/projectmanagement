#!/usr/bin/env python
import os
import sys
import django
import requests
import json
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

# Now we can import Django models
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectMember

User = get_user_model()

BASE_URL = 'http://127.0.0.1:8000/api/v1'

def test_api_endpoints():
    """
    Test API endpoints after fixing the issues
    """
    # Login to get access token
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    
    login_url = f"{BASE_URL}/auth/jwt/create/"
    login_data = {
        "username": username,
        "password": password
    }
    
    print(f"Logging in as {username}...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.json())
        return
    
    tokens = response.json()
    access_token = tokens.get('access')
    
    if not access_token:
        print("No access token received.")
        return
    
    print("Login successful, access token received.")
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"JWT {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get a project for testing
    projects_url = f"{BASE_URL}/projects/"
    response = requests.get(projects_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to get projects: {response.status_code}")
        print(response.json())
        return
    
    projects = response.json()
    if not projects:
        print("No projects found. Create a project first.")
        return
    
    project_id = projects[0]['id']
    print(f"Using project with ID: {project_id}")
    
    # Test 1: Project tasks endpoint
    print("\n1. Testing project tasks endpoint...")
    tasks_url = f"{BASE_URL}/projects/{project_id}/tasks/"
    response = requests.get(tasks_url, headers=headers)
    
    print(f"Tasks Status: {response.status_code}")
    if response.status_code == 200:
        tasks = response.json()
        print(f"Number of tasks: {len(tasks)}")
    else:
        print(response.json())
    
    # Test 2: Project members endpoint
    print("\n2. Testing project members endpoint...")
    members_url = f"{BASE_URL}/projects/{project_id}/members/"
    response = requests.get(members_url, headers=headers)
    
    print(f"Members Status: {response.status_code}")
    if response.status_code == 200:
        members = response.json()
        print(f"Number of members: {len(members)}")
    else:
        print(response.json())
    
    # Test 3: Project activity logs endpoint
    print("\n3. Testing project activity logs endpoint...")
    logs_url = f"{BASE_URL}/projects/{project_id}/activity_logs/"
    response = requests.get(logs_url, headers=headers)
    
    print(f"Activity Logs Status: {response.status_code}")
    if response.status_code == 200:
        logs = response.json()
        print(f"Number of activity logs: {len(logs)}")
    else:
        print(response.json())
    
    # Test 4: Add member endpoint
    print("\n4. Testing add member endpoint...")
    # Let's attempt to add a user that exists in the system
    add_member_url = f"{BASE_URL}/projects/{project_id}/add_member/"
    
    # For testing, we'll try to add the current user (which might already be a member)
    # In a real application, you'd add a different user
    user = User.objects.get(username=username)
    add_member_data = {
        "user": user.id,
        "role": "member"
    }
    
    response = requests.post(add_member_url, headers=headers, json=add_member_data)
    
    print(f"Add Member Status: {response.status_code}")
    print(response.json())
    
    # Test 5: Test priority validation with different case formats
    print("\n5. Testing priority validation with different cases...")
    
    # Create a task with lowercase priority
    column_url = f"{BASE_URL}/projects/{project_id}/boards/"
    response = requests.get(column_url, headers=headers)
    
    if response.status_code != 200 or not response.json():
        print("Failed to get boards or no boards found.")
        return
    
    board_id = response.json()[0]['id']
    
    columns_url = f"{BASE_URL}/projects/{project_id}/boards/{board_id}/columns/"
    response = requests.get(columns_url, headers=headers)
    
    if response.status_code != 200 or not response.json():
        print("Failed to get columns or no columns found.")
        return
    
    column_id = response.json()[0]['id']
    
    # Create a task with different priority case formats
    priorities = ["high", "HIGH", "High", "meDium", "LOW"]
    
    for priority in priorities:
        task_data = {
            "title": f"Test Task with {priority} priority",
            "description": "Testing priority validation",
            "column": column_id,
            "priority": priority
        }
        
        task_url = f"{BASE_URL}/tasks/"
        response = requests.post(task_url, headers=headers, json=task_data)
        
        print(f"Create task with '{priority}' priority status: {response.status_code}")
        if response.status_code == 201:
            print("Task created successfully!")
        else:
            print(response.json())

if __name__ == "__main__":
    test_api_endpoints()
