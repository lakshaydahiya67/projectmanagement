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
from projects.models import Project

def get_auth_token():
    """Get authentication token for testing"""
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ No active users found")
            return None
            
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        print(f"✅ Using user: {user.username} (ID: {user.id})")
        return access_token, user
        
    except Exception as e:
        print(f"❌ Token generation error: {e}")
        return None

def test_nested_routing():
    """Test all nested routing patterns"""
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
    
    try:
        project = Project.objects.filter(members__user=user).first()
        if not project:
            print("❌ No projects found for user")
            return
            
        print(f"✅ Testing with project: {project.name} (ID: {project.id})")
        
        # Test URLs to verify
        test_urls = [
            # Project level
            f"/api/v1/projects/{project.id}/",
            f"/api/v1/projects/{project.id}/boards/",
            
            # Board level (need to get a board first)
            None,  # Will be filled after getting board
            None,  # Will be filled after getting board
            
            # Column level (need to get a column first)
            None,  # Will be filled after getting column
            
            # Task level (need to get a task first)
            None,  # Will be filled after getting task
        ]
        
        print(f"\n🔍 Testing nested routing patterns:")
        print("=" * 60)
        
        # 1. Test project access
        project_url = f"{base_url}/api/v1/projects/{project.id}/"
        response = requests.get(project_url, headers=headers)
        print(f"✅ Project GET: {response.status_code} - {project_url}")
        
        # 2. Test boards listing
        boards_url = f"{base_url}/api/v1/projects/{project.id}/boards/"
        response = requests.get(boards_url, headers=headers)
        print(f"✅ Boards GET: {response.status_code} - {boards_url}")
        
        if response.status_code == 200:
            boards_data = response.json()
            if isinstance(boards_data, dict) and 'results' in boards_data:
                boards = boards_data['results']
            else:
                boards = boards_data
                
            if boards:
                board_id = boards[0]['id']
                board_name = boards[0]['name']
                print(f"   Using board: {board_name} (ID: {board_id})")
                
                # 3. Test board detail
                board_detail_url = f"{base_url}/api/v1/projects/{project.id}/boards/{board_id}/"
                response = requests.get(board_detail_url, headers=headers)
                print(f"✅ Board Detail GET: {response.status_code} - {board_detail_url}")
                
                # 4. Test columns listing
                columns_url = f"{base_url}/api/v1/projects/{project.id}/boards/{board_id}/columns/"
                response = requests.get(columns_url, headers=headers)
                print(f"✅ Columns GET: {response.status_code} - {columns_url}")
                
                if response.status_code == 200:
                    columns_data = response.json()
                    if isinstance(columns_data, dict) and 'results' in columns_data:
                        columns = columns_data['results']
                    else:
                        columns = columns_data
                        
                    if columns:
                        column_id = columns[0]['id']
                        column_name = columns[0]['name']
                        print(f"   Using column: {column_name} (ID: {column_id})")
                        
                        # 5. Test column detail
                        column_detail_url = f"{base_url}/api/v1/projects/{project.id}/boards/{board_id}/columns/{column_id}/"
                        response = requests.get(column_detail_url, headers=headers)
                        print(f"✅ Column Detail GET: {response.status_code} - {column_detail_url}")
                        
                        # 6. Test tasks listing
                        tasks_url = f"{base_url}/api/v1/projects/{project.id}/boards/{board_id}/columns/{column_id}/tasks/"
                        response = requests.get(tasks_url, headers=headers)
                        print(f"✅ Tasks GET: {response.status_code} - {tasks_url}")
                        
                        if response.status_code == 200:
                            tasks_data = response.json()
                            if isinstance(tasks_data, dict) and 'results' in tasks_data:
                                tasks = tasks_data['results']
                            else:
                                tasks = tasks_data
                                
                            if tasks:
                                task_id = tasks[0]['id']
                                task_title = tasks[0]['title']
                                print(f"   Using task: {task_title} (ID: {task_id})")
                                
                                # 7. Test task detail
                                task_detail_url = f"{base_url}/api/v1/projects/{project.id}/boards/{board_id}/columns/{column_id}/tasks/{task_id}/"
                                response = requests.get(task_detail_url, headers=headers)
                                print(f"✅ Task Detail GET: {response.status_code} - {task_detail_url}")
                            else:
                                print(f"   No tasks found in column")
                        else:
                            print(f"❌ Tasks listing failed: {response.status_code}")
                    else:
                        print(f"   No columns found in board")
                else:
                    print(f"❌ Columns listing failed: {response.status_code}")
            else:
                print(f"   No boards found in project")
        else:
            print(f"❌ Boards listing failed: {response.status_code}")
            
        print(f"\n🎯 Testing direct API endpoints:")
        print("=" * 40)
        
        # Test direct API endpoints (non-nested)
        direct_endpoints = [
            "/api/v1/tasks/",
            "/api/v1/boards/",
            "/api/v1/projects/",
        ]
        
        for endpoint in direct_endpoints:
            full_url = f"{base_url}{endpoint}"
            response = requests.get(full_url, headers=headers)
            print(f"✅ Direct {endpoint}: {response.status_code}")
                
        print(f"\n🎉 Nested routing test complete!")
                
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔧 TESTING NESTED ROUTING PATTERNS")
    print("=" * 60)
    test_nested_routing()
