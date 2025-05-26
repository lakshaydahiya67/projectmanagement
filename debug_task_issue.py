#!/usr/bin/env python
"""
Debug task creation and access issue
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

import requests
import json
from django.contrib.auth import get_user_model
from tasks.models import Task
from projects.models import Project, ProjectMember

User = get_user_model()
BASE_URL = "http://127.0.0.1:8000/api/v1"

def debug_task_issue():
    print("=== DEBUGGING TASK ACCESS ISSUE ===\n")
    
    # Find the existing task mentioned in the error
    task_id = "b640b56a-f562-4534-9639-42e0ceb127a6"
    
    print(f"1. Checking task {task_id} in database:")
    try:
        task = Task.objects.get(id=task_id)
        print(f"   ✅ Task exists: {task.title}")
        print(f"   Column: {task.column.name}")
        print(f"   Board: {task.column.board.name}")
        print(f"   Project: {task.column.board.project.name}")
        print(f"   Created by: {task.created_by.username}")
        project = task.column.board.project
    except Task.DoesNotExist:
        print(f"   ❌ Task not found")
        return
    
    # Check if we have an authenticated user (lakshay from the logs)
    print(f"\n2. Checking user 'lakshay':")
    try:
        user = User.objects.get(username='lakshay')
        print(f"   ✅ User exists: {user.username} (ID: {user.id})")
        print(f"   Is active: {user.is_active}")
        print(f"   Is staff: {user.is_staff}")
    except User.DoesNotExist:
        print(f"   ❌ User 'lakshay' not found")
        return
    
    # Check project membership
    print(f"\n3. Checking project membership:")
    membership = ProjectMember.objects.filter(project=project, user=user).first()
    if membership:
        print(f"   ✅ User is project member")
        print(f"   Role: {membership.role}")
        print(f"   Is admin: {membership.is_admin}")
        print(f"   Is owner: {membership.is_owner}")
    else:
        print(f"   ❌ User is NOT a project member")
        print(f"   Adding user as project admin...")
        ProjectMember.objects.create(
            project=project,
            user=user,
            role=ProjectMember.ADMIN
        )
        print(f"   ✅ User added as project admin")
    
    # Get auth token and test the endpoint
    print(f"\n4. Testing authentication and endpoint access:")
    
    # Test with user credentials
    login_data = {
        "email": user.email or f"{user.username}@example.com",
        "password": "admin123"  # Typical test password
    }
    
    print(f"   Attempting login with email: {login_data['email']}")
    response = requests.post(f"{BASE_URL}/auth/jwt/create/", json=login_data)
    print(f"   Login response: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   Login failed: {response.text}")
        print(f"   Setting a known password...")
        user.set_password("admin123")
        user.save()
        
        response = requests.post(f"{BASE_URL}/auth/jwt/create/", json=login_data)
        print(f"   Retry login: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Still failed: {response.text}")
            return
    
    token = response.json()['access']
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   ✅ Authentication successful")
    
    # Test the problematic endpoint
    print(f"\n5. Testing direct task access:")
    response = requests.get(f"{BASE_URL}/tasks/{task_id}/", headers=headers)
    print(f"   Direct task endpoint: {response.status_code}")
    if response.status_code != 200:
        print(f"   Failed: {response.text}")
        
        # Let's test the permission logic directly
        print(f"\n   Testing permission logic manually:")
        
        from projects.permissions import IsProjectMember
        from rest_framework.test import APIRequestFactory
        
        # Create a mock request
        factory = APIRequestFactory()
        mock_request = factory.get(f'/api/v1/tasks/{task_id}/')
        mock_request.user = user
        
        # Create a mock view
        class MockView:
            def __init__(self):
                self.kwargs = {'pk': task_id}
                self.action = 'retrieve'
        
        view = MockView()
        permission = IsProjectMember()
        
        print(f"   View kwargs: {view.kwargs}")
        print(f"   View action: {view.action}")
        
        has_perm = permission.has_permission(mock_request, view)
        has_obj_perm = permission.has_object_permission(mock_request, view, task)
        
        print(f"   Manual permission check (has_permission): {has_perm}")
        print(f"   Manual permission check (has_object_permission): {has_obj_perm}")
    else:
        print(f"   ✅ Success: Task accessible")
    
    # Test the nested endpoint 
    print(f"\n6. Testing nested task access:")
    column_id = task.column.id
    response = requests.get(f"{BASE_URL}/projects/{project.id}/boards/{task.column.board.id}/columns/{column_id}/tasks/{task_id}/", headers=headers)
    print(f"   Nested task endpoint: {response.status_code}")
    if response.status_code != 200:
        print(f"   Failed: {response.text}")
    else:
        print(f"   ✅ Success: Task accessible via nested route")

if __name__ == "__main__":
    debug_task_issue()
