#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the path
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project, Column, Board, ProjectMember

User = get_user_model()

# Get test data
user = User.objects.filter(username='lakshay').first()
if not user:
    print("❌ User 'lakshay' not found")
    exit(1)

print(f"User: {user.username} (ID: {user.id})")

# Get projects the user is a member of
memberships = ProjectMember.objects.filter(user=user)
print(f"\nUser is a member of {memberships.count()} projects:")

for membership in memberships:
    project = membership.project
    print(f"\n📁 Project: {project.name} (ID: {project.id})")
    print(f"   Role: {membership.role}")
    
    # Get boards for this project
    boards = Board.objects.filter(project=project)
    print(f"   Boards: {boards.count()}")
    
    for board in boards:
        print(f"   📋 Board: {board.name} (ID: {board.id})")
        
        # Get columns for this board
        columns = Column.objects.filter(board=board)
        print(f"      Columns: {columns.count()}")
        
        for column in columns:
            print(f"      📝 Column: {column.name} (ID: {column.id})")
            task_count = column.tasks.count()
            print(f"         Tasks: {task_count}")

# If we have projects, let's use the first column
if memberships.exists():
    first_project = memberships.first().project
    first_board = Board.objects.filter(project=first_project).first()
    if first_board:
        first_column = Column.objects.filter(board=first_board).first()
        if first_column:
            print(f"\n✅ RECOMMENDED FOR TESTING:")
            print(f"   Project: {first_project.name} (ID: {first_project.id})")
            print(f"   Board: {first_board.name} (ID: {first_board.id})")
            print(f"   Column: {first_column.name} (ID: {first_column.id})")
