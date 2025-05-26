#!/usr/bin/env python
"""
Debug board creation permission issue
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
from organizations.models import Organization, OrganizationMember
from projects.models import Project, ProjectMember, Board

User = get_user_model()

BASE_URL = "http://localhost:8001/api/v1"

def debug_board_permission():
    """Debug the board creation permission issue"""
    
    print("=" * 70)
    print(" DEBUGGING BOARD CREATION PERMISSION ISSUE")
    print("=" * 70)
    
    # Create unique identifiers
    timestamp = int(time.time())
    random_id = random.randint(1000, 9999)
    
    # Create user and get authentication
    user_data = {
        "username": f"debug_board_{timestamp}_{random_id}",
        "email": f"debug.board.{timestamp}.{random_id}@example.com", 
        "password": "TestPass123!",
        "re_password": "TestPass123!",
        "first_name": "Debug",
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
    org_data = {"name": f"Debug Org {timestamp}", "description": "Debug organization"}
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
        "name": f"Debug Project {timestamp}",
        "description": "Debug project", 
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
    
    # Check database state directly
    print(f"\n4. Checking database state")
    try:
        db_project = Project.objects.get(id=project_id)
        print(f"   ✅ Project exists in DB: {db_project.name}")
        
        # Check if user is a project member
        project_membership = ProjectMember.objects.filter(project=db_project, user=user).first()
        if project_membership:
            print(f"   ✅ User is project member with role: {project_membership.role}")
            print(f"   ✅ User is_admin: {project_membership.is_admin}")
            print(f"   ✅ User is_owner: {project_membership.is_owner}")
        else:
            print("   ❌ User is NOT a project member")
            
        # Check if user is org member
        org_membership = OrganizationMember.objects.filter(organization=db_project.organization, user=user).first()
        if org_membership:
            print(f"   ✅ User is org member with role: {org_membership.role}")
        else:
            print("   ❌ User is NOT an org member")
            
        # Check if default board was created
        default_boards = Board.objects.filter(project=db_project, is_default=True)
        print(f"   Default boards found: {default_boards.count()}")
        for board in default_boards:
            print(f"     - {board.name} (ID: {board.id})")
            
    except Project.DoesNotExist:
        print("   ❌ Project not found in database")
        return
    except Exception as e:
        print(f"   ❌ Database check error: {e}")
        return
    
    # Try board creation
    print(f"\n5. Attempting board creation")
    board_data = {"name": f"Debug Board {timestamp}", "description": "Debug board"}
    response = requests.post(f"{BASE_URL}/projects/{project_id}/boards/", json=board_data, headers=headers)
    print(f"   Board creation: {response.status_code}")
    if response.status_code != 201:
        print(f"   Board creation failed: {response.text}")
        
        # Let's also try to access the project members endpoint to verify permissions
        print(f"\n6. Testing project members endpoint for permission verification")
        response = requests.get(f"{BASE_URL}/projects/{project_id}/members/", headers=headers)
        print(f"   Members endpoint: {response.status_code}")
        if response.status_code == 200:
            members = response.json()
            print(f"   ✅ Found {len(members)} members:")
            for member in members:
                print(f"     - {member['user']['username']} ({member['role']})")
        else:
            print(f"   ❌ Members endpoint failed: {response.text}")
    else:
        board = response.json()
        print(f"   ✅ Board created: {board['id']}")

if __name__ == "__main__":
    debug_board_permission()
