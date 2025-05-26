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

def test_task_priorities():
    """Test task creation with different priority values"""
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
    
    # Get a project and default board
    try:
        project = Project.objects.filter(members__user=user).first()
        if not project:
            print("❌ No projects found for user")
            return
            
        print(f"✅ Testing with project: {project.name} (ID: {project.id})")
        
        # Get default board
        boards_url = f"{base_url}/api/v1/projects/{project.id}/boards/"
        response = requests.get(boards_url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to get boards: {response.text}")
            return
            
        boards_data = response.json()
        
        # Handle both paginated and non-paginated responses
        if isinstance(boards_data, dict) and 'results' in boards_data:
            boards = boards_data['results']
        else:
            boards = boards_data
            
        default_board = None
        
        for board in boards:
            if isinstance(board, dict) and board.get('is_default', False):
                default_board = board
                break
                
        if not default_board:
            print("❌ No default board found")
            return
            
        print(f"✅ Using default board: {default_board['name']} (ID: {default_board['id']})")
        
        # Get columns
        columns_url = f"{base_url}/api/v1/projects/{project.id}/boards/{default_board['id']}/columns/"
        columns_response = requests.get(columns_url, headers=headers)
        
        if columns_response.status_code != 200:
            print(f"❌ Failed to get columns: {columns_response.text}")
            return
            
        columns_data = columns_response.json()
        
        # Handle both paginated and non-paginated responses
        if isinstance(columns_data, dict) and 'results' in columns_data:
            columns = columns_data['results']
        else:
            columns = columns_data
            
        if not columns:
            print("❌ No columns found")
            return
            
        column_id = columns[0]['id']
        print(f"✅ Using column: {columns[0]['name']} (ID: {column_id})")
        
        # Test all priority values
        priority_values = ['low', 'medium', 'high', 'urgent']
        tasks_url = f"{base_url}/api/v1/projects/{project.id}/boards/{default_board['id']}/columns/{column_id}/tasks/"
        
        print(f"\n🎯 Testing task creation with different priorities:")
        print("=" * 60)
        
        for priority in priority_values:
            task_data = {
                "title": f"Test Task - {priority.capitalize()} Priority",
                "description": f"Testing {priority} priority value",
                "priority": priority
            }
            
            print(f"\n📝 Creating task with priority: {priority}")
            response = requests.post(tasks_url, headers=headers, json=task_data)
            
            if response.status_code == 201:
                created_task = response.json()
                print(f"✅ SUCCESS: Task created with priority '{created_task['priority']}' (Display: {created_task['priority_display']})")
                print(f"   Task ID: {created_task['id']}")
                print(f"   Title: {created_task['title']}")
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"   Response: {response.text}")
                
        print(f"\n🎉 Priority testing complete!")
                
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔧 TESTING TASK CREATION WITH ALL PRIORITY VALUES")
    print("=" * 60)
    test_task_priorities()
