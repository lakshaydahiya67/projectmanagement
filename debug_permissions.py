#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the path
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project, ProjectMember

User = get_user_model()

# Debug permission issue
user = User.objects.filter(username='lakshay').first()
project_id = '93056c8a-c381-4da3-9eb5-471c917b8e83'

print(f"User: {user.username} (ID: {user.id})")
print(f"Project ID: {project_id}")

# Check project membership
membership = ProjectMember.objects.filter(
    project_id=project_id,
    user=user
).first()

if membership:
    print(f"✅ User IS a member of the project")
    print(f"   Role: {membership.role}")
    print(f"   Is admin: {membership.is_admin}")
    print(f"   Is owner: {membership.is_owner}")
else:
    print("❌ User is NOT a member of the project")

# Check project details
try:
    project = Project.objects.get(id=project_id)
    print(f"Project: {project.name}")
    print(f"Is public: {project.is_public}")
    print(f"Organization: {project.organization.name}")
except Project.DoesNotExist:
    print("❌ Project does not exist")

# Check if user is in organization
from organizations.models import OrganizationMember
org_membership = OrganizationMember.objects.filter(
    organization=project.organization,
    user=user
).first()

if org_membership:
    print(f"✅ User IS a member of the organization")
    print(f"   Role: {org_membership.role}")
else:
    print("❌ User is NOT a member of the organization")
