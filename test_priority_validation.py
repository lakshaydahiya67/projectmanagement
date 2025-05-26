#!/usr/bin/env python3
import os
import django
import sys
import json

# Add the project directory to Python path
sys.path.insert(0, '/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from users.models import User
from projects.models import Project, ProjectMember

def get_auth_token():
    """Get authentication token for testing"""
    # Try to get existing user
    try:
        user = User.objects.get(username='lakshay')
        print(f"✅ Using existing user: {user.email} ({user.username})")
        return None, user  # No token needed, will use force_authenticate
    except User.DoesNotExist:
        print("❌ User not found")
        return None

def test_priority_validation():
    """Test priority validation with different case formats"""
    base_url = "http://127.0.0.1:8001"
    
    # Set the Host header explicitly
    headers_base = {
        'Host': '127.0.0.1:8001',
        'Content-Type': 'application/json'
    }
    
    # Get authentication
    auth_data = get_auth_token()
    if not auth_data:
        return
        
    token, user = auth_data
    
    # Create API client with authentication
    from rest_framework.test import APITestCase, APIClient
    from django.conf import settings
    
    # Add testserver to ALLOWED_HOSTS temporarily
    settings.ALLOWED_HOSTS.append('testserver')
    
    # Create client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Get a project and column
    project = Project.objects.filter(members__user=user).first()
    if not project:
        print("❌ No projects found for user")
        return
        
    print(f"✅ Testing with project: {project.name}")
    
    # Test priority values
    test_cases = [
        ('low', True),
        ('LOW', True),  # Should work with our fix
        ('Medium', True),  # Should work with our fix
        ('high', True),
        ('HIGH', True),  # Should work with our fix
        ('urgent', True),
        ('URGENT', True),  # Should work with our fix
        ('invalid', False),  # Should fail
    ]
    
    # Use direct task creation endpoint
    tasks_url = f"/api/v1/tasks/"
    column_id = "67ee1693-2469-40db-a4f6-46f7827a8a65"  # Known good column ID
    
    print(f"\n🎯 Testing priority validation:")
    print("=" * 60)
    
    for priority, should_succeed in test_cases:
        task_data = {
            "title": f"Test Priority {priority}",
            "description": f"Testing priority: {priority}",
            "priority": priority,
            "column": column_id,
            "due_date": "2025-05-26"
        }
        
        print(f"\n📝 Testing priority: '{priority}' (expecting {'SUCCESS' if should_succeed else 'FAILURE'})")
        response = client.post(tasks_url, task_data, format='json')
        
        if should_succeed:
            if response.status_code == 201:
                created_task = response.data
                print(f"✅ SUCCESS: Task created with priority '{created_task['priority']}'")
                # Clean up - delete the test task
                delete_url = f"/api/v1/tasks/{created_task['id']}/"
                client.delete(delete_url)
            else:
                print(f"❌ FAILED (Expected success): Status {response.status_code}")
                print(f"   Response: {response.data if hasattr(response, 'data') else 'Unknown error'}")
        else:
            if response.status_code != 201:
                print(f"✅ CORRECTLY FAILED: Status {response.status_code}")
                print(f"   Error: {response.data.get('priority', 'Unknown error') if hasattr(response, 'data') else 'Unknown error'}")
            else:
                print(f"❌ UNEXPECTEDLY SUCCEEDED: Should have failed but didn't")
                # Clean up if it unexpectedly succeeded
                created_task = response.data
                delete_url = f"/api/v1/tasks/{created_task['id']}/"
                client.delete(delete_url)

if __name__ == '__main__':
    print("🔧 TESTING PRIORITY VALIDATION")
    print("=" * 60)
    print(f"Python path: {sys.path}")
    try:
        test_priority_validation()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
