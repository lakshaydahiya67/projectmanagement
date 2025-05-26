#!/usr/bin/env python
"""
Test script to verify API endpoints are working correctly after permission fixes
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tasks.models import Task
from projects.models import Project

def test_task_endpoints():
    """Test task endpoints to verify our permission fixes"""
    
    # Get the task and user
    try:
        task = Task.objects.get(id='b640b56a-f562-4534-9639-42e0ceb127a6')
        User = get_user_model()
        user = User.objects.get(username='lakshay')
        
        print(f"Testing with task: {task.title} (ID: {task.id})")
        print(f"User: {user.username}")
        project = task.column.board.project
        print(f"Project: {project.name} (ID: {project.id})")
        
    except Exception as e:
        print(f"Error getting test data: {e}")
        return False
    
    # Create API client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Test 1: Direct task access (this was failing with 403)
    print("\n=== Test 1: Direct Task Access ===")
    response = client.get(f'/api/v1/tasks/{task.id}/')
    print(f"GET /api/v1/tasks/{task.id}/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Direct task access works!")
        print(f"   Task title: {response.data.get('title', 'N/A')}")
    else:
        print("❌ FAILED: Direct task access still failing")
        if hasattr(response, 'data'):
            print(f"   Error: {response.data}")
    
    # Test 2: Task list
    print("\n=== Test 2: Task List ===")
    response = client.get('/api/v1/tasks/')
    print(f"GET /api/v1/tasks/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ SUCCESS: Task list works! Found {len(response.data)} tasks")
    else:
        print("❌ FAILED: Task list not working")
        if hasattr(response, 'data'):
            print(f"   Error: {response.data}")
    
    # Test 3: Nested task access investigation
    print("\n=== Test 3: Nested Task Access Investigation ===")
    
    # The URL /api/v1/projects/{id}/tasks/{task_id}/ does NOT exist in the routing structure
    # Based on URL pattern analysis, the correct nested routing is:
    # /api/v1/projects/{project_id}/boards/{board_id}/columns/{column_id}/tasks/{task_id}/
    
    print("Testing actual nested routing pattern...")
    try:
        # Get project boards first
        boards_response = client.get(f'/api/v1/projects/{project.id}/boards/')
        if boards_response.status_code == 200:
            boards_data = boards_response.data
            if 'results' in boards_data and boards_data['results']:
                board = boards_data['results'][0]
                board_id = board['id']
                
                # Get board columns
                columns_response = client.get(f'/api/v1/projects/{project.id}/boards/{board_id}/columns/')
                if columns_response.status_code == 200:
                    columns_data = columns_response.data
                    if 'results' in columns_data and columns_data['results']:
                        column = columns_data['results'][0]
                        column_id = column['id']
                        
                        # Test nested tasks access (correct pattern)
                        nested_tasks_url = f'/api/v1/projects/{project.id}/boards/{board_id}/columns/{column_id}/tasks/'
                        nested_response = client.get(nested_tasks_url)
                        print(f"GET {nested_tasks_url} - Status: {nested_response.status_code}")
                        
                        if nested_response.status_code == 200:
                            print("✅ SUCCESS: Nested task access works with correct URL pattern!")
                            
                            # Test specific task access via nested route
                            nested_tasks_data = nested_response.data
                            if 'results' in nested_tasks_data and nested_tasks_data['results']:
                                nested_task_id = nested_tasks_data['results'][0]['id']
                                nested_task_url = f'/api/v1/projects/{project.id}/boards/{board_id}/columns/{column_id}/tasks/{nested_task_id}/'
                                task_response = client.get(nested_task_url)
                                print(f"GET {nested_task_url} - Status: {task_response.status_code}")
                                if task_response.status_code == 200:
                                    print("✅ SUCCESS: Nested task detail access works!")
                                else:
                                    print("❌ FAILED: Nested task detail access failed")
                        else:
                            print("❌ FAILED: Nested task access failed with correct pattern")
                    else:
                        print("No columns found in board")
                else:
                    print(f"Failed to get columns: {columns_response.status_code}")
            else:
                print("No boards found in project")
        else:
            print(f"Failed to get boards: {boards_response.status_code}")
    except Exception as e:
        print(f"Exception during nested routing test: {e}")
    
    # Test the non-existent URL pattern to confirm it fails
    print(f"\nTesting non-existent URL pattern:")
    failed_response = client.get(f'/api/v1/projects/{project.id}/tasks/{task.id}/')
    print(f"GET /api/v1/projects/{project.id}/tasks/{task.id}/ - Status: {failed_response.status_code}")
    print("❌ CONFIRMED: The URL pattern /projects/{id}/tasks/{task_id}/ does NOT exist in the API")
    
    # Test 4: Task creation
    print("\n=== Test 4: Task Creation ===")
    new_task_data = {
        'title': 'Test Task Creation',
        'description': 'Testing if task creation works after fix',
        'column': '67ee1693-2469-40db-a4f6-46f7827a8a65',  # Use a valid column ID
        'priority': 'medium'  # Use lowercase priority
    }
    
    response = client.post('/api/v1/tasks/', new_task_data)
    print(f"POST /api/v1/tasks/ - Status: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ SUCCESS: Task creation works!")
        created_task_id = response.data.get('id')
        print(f"   Created task ID: {created_task_id}")
        
        # Clean up - delete the test task
        delete_response = client.delete(f'/api/v1/tasks/{created_task_id}/')
        print(f"   Cleanup delete - Status: {delete_response.status_code}")
        
    else:
        print("❌ FAILED: Task creation not working")
        if hasattr(response, 'data'):
            print(f"   Error: {response.data}")
    
    # Test 5: Priority Case Sensitivity
    print("\n=== Test 5: Priority Case Sensitivity ===")
    print("Testing different priority case formats...")
    
    # Test different priority cases
    priority_tests = [
        ('low', 'lowercase'),
        ('LOW', 'uppercase'), 
        ('Medium', 'mixed case'),
        ('HIGH', 'uppercase'),
        ('urgent', 'lowercase')
    ]
    
    for priority, case_type in priority_tests:
        test_task_data = {
            'title': f'Priority Test - {case_type}',
            'description': f'Testing {case_type} priority: {priority}',
            'column': '67ee1693-2469-40db-a4f6-46f7827a8a65',
            'priority': priority
        }
        
        response = client.post('/api/v1/tasks/', test_task_data)
        if response.status_code == 201:
            print(f"✅ {priority} ({case_type}) -> SUCCESS")
            # Clean up
            task_id = response.data.get('id')
            client.delete(f'/api/v1/tasks/{task_id}/')
        else:
            print(f"❌ {priority} ({case_type}) -> FAILED: {response.data if hasattr(response, 'data') else 'Unknown error'}")

    # Test 6: Project endpoints (to check for 404 errors)
    print("\n=== Test 6: Project Endpoints ===")
    response = client.get('/api/v1/projects/')
    print(f"GET /api/v1/projects/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ SUCCESS: Project list works! Found {len(response.data)} projects")
    else:
        print("❌ FAILED: Project list not working")
        if hasattr(response, 'data'):
            print(f"   Error: {response.data}")
    
    print("\n=== Test Summary ===")
    return True

if __name__ == '__main__':
    # Add testserver to allowed hosts temporarily
    from django.conf import settings
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')
    
    test_task_endpoints()
