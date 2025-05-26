#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the path
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from projects.models import Project, Column, Board
import json

User = get_user_model()

# Get test data
user = User.objects.filter(username='lakshay').first()
if not user:
    print("❌ User 'lakshay' not found")
    exit(1)

project = Project.objects.filter(name='newww').first()
if not project:
    print("❌ Project 'newww' not found")
    exit(1)

# Get a column from this project
board = Board.objects.filter(project=project).first()
if not board:
    print("❌ No board found for project")
    exit(1)

column = Column.objects.filter(board=board).first()
if not column:
    print("❌ No column found for board")
    exit(1)

print(f"Testing task creation for:")
print(f"  User: {user.username}")
print(f"  Project: {project.name} (ID: {project.id})")
print(f"  Board: {board.name} (ID: {board.id})")
print(f"  Column: {column.name} (ID: {column.id})")

# Test API endpoints
client = Client()
client.force_login(user)

print("\n=== Testing Task Creation ===")

# Test task creation
task_data = {
    'title': 'Test Task Creation',
    'description': 'Testing if task creation works',
    'column': str(column.id),
    'priority': 'medium'
}

print(f"POST data: {task_data}")
response = client.post('/api/v1/tasks/', data=task_data, content_type='application/json')
print(f"POST /api/v1/tasks/ - Status: {response.status_code}")

if response.status_code != 201:
    print(f"   Error: {response.content.decode()}")
    try:
        error_data = response.json()
        print(f"   Error JSON: {error_data}")
    except:
        pass
else:
    print("✅ SUCCESS: Task creation works!")
    task_data = response.json()
    print(f"   Created task: {task_data.get('title')} (ID: {task_data.get('id')})")
