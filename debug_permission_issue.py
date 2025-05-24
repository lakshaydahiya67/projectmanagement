#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Add the project directory to the Python path
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from users.models import User
from projects.models import Project, ProjectMember, Column, Board
from organizations.models import Organization, OrganizationMember

def debug_permission_issue():
    print("=== DEBUG PERMISSION ISSUE ===")
    
    # Get the test user and project
    try:
        user = User.objects.get(username='testuser')
        print(f"✅ User found: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        print("❌ Test user not found")
        return
    
    try:
        project = Project.objects.get(name='Test Project Debug')
        print(f"✅ Project found: {project.name} (ID: {project.id})")
        print(f"   - Is public: {project.is_public}")
        print(f"   - Organization: {project.organization.name}")
    except Project.DoesNotExist:
        print("❌ Test project not found")
        return
    
    # Check project membership
    project_member = ProjectMember.objects.filter(project=project, user=user).first()
    if project_member:
        print(f"✅ User is project member with role: {project_member.role}")
    else:
        print("❌ User is NOT a project member")
    
    # Check organization membership
    org_member = OrganizationMember.objects.filter(organization=project.organization, user=user).first()
    if org_member:
        print(f"✅ User is organization member with role: {org_member.role}")
    else:
        print("❌ User is NOT an organization member")
    
    # Get board and column
    try:
        board = Board.objects.get(project=project)
        print(f"✅ Board found: {board.name} (ID: {board.id})")
        
        column = Column.objects.filter(board=board).first()
        if column:
            print(f"✅ Column found: {column.name} (ID: {column.id})")
        else:
            print("❌ No columns found in board")
            return
    except Board.DoesNotExist:
        print("❌ Board not found for project")
        return
    
    # Test the permission logic manually
    print("\n=== MANUAL PERMISSION CHECK ===")
    
    # Simulate the request data that would be sent for task creation
    request_data = {
        'column': column.id,
        'title': 'Test Task for Permission Debug',
        'description': 'Testing permission logic'
    }
    
    print(f"Request data: {request_data}")
    
    # Check if we can extract project ID from column
    try:
        test_column = Column.objects.get(id=request_data['column'])
        extracted_project_id = test_column.board.project_id
        print(f"✅ Extracted project ID from column: {extracted_project_id}")
        
        # Check if this matches our project
        if extracted_project_id == project.id:
            print("✅ Project ID matches")
        else:
            print(f"❌ Project ID mismatch: expected {project.id}, got {extracted_project_id}")
            
        # Check project membership for this extracted project
        is_member = ProjectMember.objects.filter(
            project_id=extracted_project_id,
            user=user
        ).exists()
        print(f"Project membership check result: {is_member}")
        
    except Column.DoesNotExist:
        print(f"❌ Column {request_data['column']} does not exist")
    
    # Now test the actual API call
    print("\n=== ACTUAL API TEST ===")
    
    # Login to get token
    login_response = requests.post('http://localhost:8000/api/v1/auth/login/', data={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    if login_response.status_code == 200:
        token = login_response.json()['access']
        print("✅ Successfully obtained auth token")
        
        # Try to create a task
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        task_data = {
            'column': column.id,
            'title': 'Permission Debug Task',
            'description': 'Testing task creation permission'
        }
        
        print(f"Creating task with data: {task_data}")
        
        response = requests.post('http://localhost:8000/api/v1/tasks/', 
                               json=task_data, 
                               headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.text}")
        
        if response.status_code == 403:
            print("❌ Permission denied - investigating...")
            
    else:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")

if __name__ == '__main__':
    debug_permission_issue()
