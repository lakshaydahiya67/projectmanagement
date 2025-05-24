#!/usr/bin/env python3
"""
Debug script to test and identify remaining critical issues:
1. Project creation with blank fields (error message specificity)
2. Project editing functionality
3. Task creation functionality  
4. Member creation functionality
5. Board view loading functionality
"""

import os
import sys
import django
import requests
import json
import uuid
from datetime import datetime
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')
django.setup()

from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMember
from projects.models import Project, ProjectMember, Board, Column
from tasks.models import Task

User = get_user_model()
BASE_URL = 'http://localhost:8000'

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def make_request(method, endpoint, data=None, token=None):
    """Helper function to make API requests"""
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'  # JWT uses Bearer authentication
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        print(f"{method} {url}")
        print(f"Status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return response.status_code, response_data
        except:
            print(f"Response (text): {response.text}")
            return response.status_code, response.text
            
    except Exception as e:
        print(f"Request failed: {e}")
        return None, str(e)

def test_project_creation_errors():
    """Test 1: Project creation with blank fields - check error message specificity"""
    print_section("TEST 1: Project Creation Error Messages")
    
    # Generate unique username and email
    timestamp = str(int(datetime.now().timestamp()))
    random_id = str(random.randint(1000, 9999))
    
    # First, create test user and get token
    user_data = {
        'username': f'testuser_debug_{timestamp}_{random_id}',
        'email': f'testuser.debug.{timestamp}.{random_id}@example.com',
        'password': 'TestPassword123!',
        're_password': 'TestPassword123!',  # Required for password confirmation
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    # Register user
    status, response = make_request('POST', '/api/v1/auth/users/', user_data)
    if status != 201:
        print(f"❌ User registration failed: {response}")
        return None
    
    user_id = response.get('id')
    print(f"✅ User registered with ID: {user_id}")
    
    # Activate user using Django ORM (bypassing email activation for testing)
    try:
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()
        print(f"✅ User activated")
    except User.DoesNotExist:
        print("❌ Failed to activate user")
        return None
    
    # Get token
    login_data = {
        'email': user_data['email'],  # Using email instead of username
        'password': user_data['password']
    }
    status, response = make_request('POST', '/api/v1/auth/jwt/create/', login_data)
    if status != 200:
        print(f"❌ Login failed: {response}")
        return None
    
    token = response.get('access')
    print(f"✅ User authenticated, token: {token[:20]}...")
    
    # Create organization first
    org_data = {
        'name': 'Test Organization',
        'description': 'Test organization for debugging'
    }
    status, response = make_request('POST', '/api/v1/organizations/', org_data, token)
    if status != 201:
        print(f"❌ Organization creation failed: {response}")
        return None
    
    org_id = response.get('id')
    print(f"✅ Organization created with ID: {org_id}")
    
    # Now test project creation with blank required fields
    print("\n--- Testing blank project name ---")
    blank_name_data = {
        'name': '',  # Blank name
        'organization': org_id,
        'description': 'Test project'
    }
    status, response = make_request('POST', '/api/v1/projects/', blank_name_data, token)
    print(f"Expected specific error for 'name' field, got: {response}")
    
    print("\n--- Testing missing organization ---")
    missing_org_data = {
        'name': 'Test Project'
        # Missing organization
    }
    status, response = make_request('POST', '/api/v1/projects/', missing_org_data, token)
    print(f"Expected specific error for 'organization' field, got: {response}")
    
    print("\n--- Testing null organization ---")
    null_org_data = {
        'name': 'Test Project',
        'organization': None
    }
    status, response = make_request('POST', '/api/v1/projects/', null_org_data, token)
    print(f"Expected specific error for 'organization' field, got: {response}")
    
    return token, org_id

def test_project_editing(token, org_id):
    """Test 2: Project editing functionality"""
    print_section("TEST 2: Project Editing Functionality")
    
    # First create a project to edit
    project_data = {
        'name': 'Project to Edit',
        'organization': org_id,
        'description': 'Original description'
    }
    status, response = make_request('POST', '/api/v1/projects/', project_data, token)
    if status != 201:
        print(f"❌ Project creation for editing test failed: {response}")
        return None
    
    project_id = response.get('id')
    print(f"✅ Project created for editing test with ID: {project_id}")
    
    # Test editing project
    print("\n--- Testing project update ---")
    update_data = {
        'name': 'Updated Project Name',
        'description': 'Updated description',
        'organization': org_id
    }
    status, response = make_request('PUT', f'/api/v1/projects/{project_id}/', update_data, token)
    print(f"Edit project result: Status {status}, Response: {response}")
    
    # Test partial update
    print("\n--- Testing partial project update ---")
    partial_data = {
        'description': 'Partially updated description'
    }
    status, response = make_request('PATCH', f'/api/v1/projects/{project_id}/', partial_data, token)
    print(f"Partial edit result: Status {status}, Response: {response}")
    
    return project_id

def test_task_creation(token, project_id):
    """Test 3: Task creation functionality"""
    print_section("TEST 3: Task Creation Functionality")
    
    # First, get the default board and column
    status, response = make_request('GET', f'/api/v1/projects/{project_id}/boards/', token=token)
    if status != 200:
        print(f"❌ Failed to get boards: {response}")
        return
    
    boards = response
    if not boards:
        print("❌ No boards found for the project")
        return
    
    board_id = boards[0]['id']
    print(f"✅ Found board with ID: {board_id}")
    
    # Get columns for the board
    status, response = make_request('GET', f'/api/v1/projects/{project_id}/boards/{board_id}/columns/', token=token)
    if status != 200:
        print(f"❌ Failed to get columns: {response}")
        return
    
    columns = response
    if not columns:
        print("❌ No columns found for the board")
        return
    
    column_id = columns[0]['id']
    print(f"✅ Found column with ID: {column_id}")
    
    # Test task creation
    print("\n--- Testing task creation ---")
    task_data = {
        'title': 'Test Task',
        'description': 'Test task description',
        'column': column_id,
        'priority': 'medium'
    }
    status, response = make_request('POST', '/api/v1/tasks/', task_data, token)
    print(f"Task creation result: Status {status}, Response: {response}")
    
    # Test task creation with blank required fields
    print("\n--- Testing task creation with blank title ---")
    blank_task_data = {
        'title': '',  # Blank title
        'column': column_id
    }
    status, response = make_request('POST', '/api/v1/tasks/', blank_task_data, token)
    print(f"Blank title task result: Status {status}, Response: {response}")

def test_member_creation(token, project_id):
    """Test 4: Member creation functionality"""
    print_section("TEST 4: Member Creation Functionality")
    
    # Generate unique username and email for member user
    timestamp = str(int(datetime.now().timestamp()))
    random_id = str(random.randint(1000, 9999))
    
    # Create another user to add as member
    user_data = {
        'username': f'member_user_{timestamp}_{random_id}',
        'email': f'member.{timestamp}.{random_id}@example.com',
        'password': 'TestPassword123!',
        're_password': 'TestPassword123!',  # Required for password confirmation
        'first_name': 'Member',
        'last_name': 'User'
    }
    
    status, response = make_request('POST', '/api/v1/auth/users/', user_data)
    if status != 201:
        print(f"❌ Member user registration failed: {response}")
        return
    
    member_user_id = response.get('id')
    print(f"✅ Member user created with ID: {member_user_id}")
    
    # Activate member user using Django ORM (bypassing email activation for testing)
    try:
        member_user = User.objects.get(id=member_user_id)
        member_user.is_active = True
        member_user.save()
        print(f"✅ Member user activated")
    except User.DoesNotExist:
        print("❌ Failed to activate member user")
        return
    
    # Test adding member to project
    print("\n--- Testing add member to project ---")
    member_data = {
        'user': member_user_id,
        'role': 'member'
    }
    status, response = make_request('POST', f'/api/v1/projects/{project_id}/add_member/', member_data, token)
    print(f"Add member result: Status {status}, Response: {response}")

def test_board_view_loading(token, project_id):
    """Test 5: Board view loading functionality"""
    print_section("TEST 5: Board View Loading Functionality")
    
    # Test getting project boards
    print("\n--- Testing get project boards ---")
    status, response = make_request('GET', f'/api/v1/projects/{project_id}/boards/', token=token)
    print(f"Get boards result: Status {status}, Response: {response}")
    
    if status == 200 and response:
        board_id = response[0]['id']
        
        # Test getting board details
        print(f"\n--- Testing get board details for board {board_id} ---")
        status, response = make_request('GET', f'/api/v1/projects/{project_id}/boards/{board_id}/', token=token)
        print(f"Get board details result: Status {status}, Response: {response}")
        
        # Test getting board columns
        print(f"\n--- Testing get board columns ---")
        status, response = make_request('GET', f'/api/v1/projects/{project_id}/boards/{board_id}/columns/', token=token)
        print(f"Get board columns result: Status {status}, Response: {response}")

def main():
    print_section("DEBUGGING REMAINING CRITICAL ISSUES")
    
    # Test 1: Project creation error messages
    result = test_project_creation_errors()
    if not result:
        print("❌ Failed to complete project creation error tests")
        return
    
    token, org_id = result
    
    # Test 2: Project editing
    project_id = test_project_editing(token, org_id)
    if not project_id:
        print("❌ Failed to complete project editing tests")
        return
    
    # Test 3: Task creation
    test_task_creation(token, project_id)
    
    # Test 4: Member creation
    test_member_creation(token, project_id)
    
    # Test 5: Board view loading
    test_board_view_loading(token, project_id)
    
    print_section("DEBUGGING COMPLETE")

if __name__ == '__main__':
    main()
