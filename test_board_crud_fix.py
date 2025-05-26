#!/usr/bin/env python3
import os
import django
import sys
import requests
import json

# Add the project directory to Python path
sys.path.insert(0, '/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from users.models import User
from projects.models import Project, ProjectMember, Board

def get_auth_token():
    """Get authentication token for testing"""
    try:
        # Try to get an existing user
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ No active users found")
            return None
            
        # Create JWT token manually for testing
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        print(f"✅ Using user: {user.username} (ID: {user.id})")
        return access_token, user
        
    except Exception as e:
        print(f"❌ Token generation error: {e}")
        return None

def test_board_crud_operations():
    """Test complete CRUD operations for boards"""
    base_url = "http://127.0.0.1:8001"
    
    # Get authentication
    auth_data = get_auth_token()
    if not auth_data:
        return
        
    token, user = auth_data
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Get a project where user is a member
    try:
        project = Project.objects.filter(members__user=user).first()
        if not project:
            print("❌ No projects found for user")
            return
            
        print(f"✅ Testing with project: {project.name} (ID: {project.id})")
        
        # Test 1: GET boards (list existing boards)
        print("\n📋 Test 1: GET /api/v1/projects/{id}/boards/")
        boards_url = f"{base_url}/api/v1/projects/{project.id}/boards/"
        
        response = requests.get(boards_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                boards = response.json()
                if isinstance(boards, dict) and 'results' in boards:
                    boards_list = boards['results']
                else:
                    boards_list = boards
                    
                print(f"✅ GET boards successful: Found {len(boards_list)} boards")
                for board in boards_list:
                    if isinstance(board, dict):
                        is_default = board.get('is_default', False)
                        default_text = " (DEFAULT)" if is_default else ""
                        print(f"  - {board.get('name', 'Unnamed')}{default_text} (ID: {board.get('id')})")
                        
                        # Store the first default board for task testing
                        if is_default and not hasattr(test_board_crud_operations, 'default_board_id'):
                            test_board_crud_operations.default_board_id = board.get('id')
                    else:
                        print(f"  - {board}")
            except Exception as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"❌ GET boards failed: {response.text}")
            
        # Test 2: OPTIONS request (check allowed methods)
        print(f"\n🔍 Test 2: OPTIONS {boards_url}")
        options_response = requests.options(boards_url, headers=headers)
        print(f"Status Code: {options_response.status_code}")
        print(f"Allowed Methods: {options_response.headers.get('Allow', 'Not specified')}")
        
        # Test 3: POST create new board
        print(f"\n➕ Test 3: POST {boards_url}")
        new_board_data = {
            "name": "Test Board via API",
            "description": "Created via automated test for debugging"
        }
        
        create_response = requests.post(boards_url, headers=headers, json=new_board_data)
        print(f"Status Code: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        
        if create_response.status_code == 201:
            created_board = create_response.json()
            print(f"✅ POST board creation successful!")
            print(f"   Created board: {created_board.get('name')} (ID: {created_board.get('id')})")
            
            # Test task creation flow with default board that has columns
            if hasattr(test_board_crud_operations, 'default_board_id'):
                print(f"\n🎯 Using default board for task creation test...")
                test_task_creation_flow(base_url, headers, project.id, test_board_crud_operations.default_board_id)
            else:
                print(f"\n⚠️  New board created but has no columns. Task creation test skipped.")
                print(f"   (Default boards created during project setup have pre-configured columns)")
                
        elif create_response.status_code == 405:
            print("❌ POST not allowed - 405 Method Not Allowed")
            print("This indicates the BoardViewSet is still not properly configured")
        else:
            print(f"❌ POST board creation failed with status {create_response.status_code}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

def test_task_creation_flow(base_url, headers, project_id, board_id):
    """Test the complete task creation flow after board creation"""
    print(f"\n🎯 Test 4: Complete Task Creation Flow")
    
    try:
        # Step 1: Get board columns
        columns_url = f"{base_url}/api/v1/projects/{project_id}/boards/{board_id}/columns/"
        print(f"Getting columns: {columns_url}")
        
        columns_response = requests.get(columns_url, headers=headers)
        print(f"Columns Status: {columns_response.status_code}")
        
        if columns_response.status_code == 200:
            columns_data = columns_response.json()
            
            # Handle both paginated and non-paginated responses
            if isinstance(columns_data, dict) and 'results' in columns_data:
                columns = columns_data['results']
            else:
                columns = columns_data
                
            print(f"✅ Found {len(columns)} columns")
            
            if columns:
                # Use first column for task creation
                column_id = columns[0]['id']
                print(f"Using column: {columns[0]['name']} (ID: {column_id})")
                
                # Step 2: Create a task in the column
                tasks_url = f"{base_url}/api/v1/projects/{project_id}/boards/{board_id}/columns/{column_id}/tasks/"
                task_data = {
                    "title": "Test Task via API",
                    "description": "Created via automated test for debugging",
                    "priority": "medium"
                }
                
                print(f"Creating task: {tasks_url}")
                task_response = requests.post(tasks_url, headers=headers, json=task_data)
                print(f"Task Creation Status: {task_response.status_code}")
                print(f"Task Response: {task_response.text}")
                
                if task_response.status_code == 201:
                    print("🎉 COMPLETE SUCCESS! Task creation works end-to-end!")
                    created_task = task_response.json()
                    print(f"   Created task: {created_task.get('title')} (ID: {created_task.get('id')})")
                else:
                    print(f"❌ Task creation failed with status {task_response.status_code}")
            else:
                print("❌ No columns found in the board")
        else:
            print(f"❌ Failed to get columns: {columns_response.text}")
            
    except Exception as e:
        print(f"❌ Task creation flow error: {e}")

if __name__ == '__main__':
    print("🔧 TESTING BOARD CRUD OPERATIONS AFTER ROUTING FIX")
    print("=" * 60)
    test_board_crud_operations()
