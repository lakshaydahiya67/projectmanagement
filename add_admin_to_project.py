#!/usr/bin/env python3
import os
import django
import sys
import traceback

# Add the project directory to the path
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
try:
    django.setup()
    print("Django setup successful")
except Exception as e:
    print(f"Django setup failed: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

from django.contrib.auth import get_user_model
from projects.models import Project, ProjectMember
from organizations.models import Organization, OrganizationMember

User = get_user_model()

def add_admin_to_project():
    """Add the admin user to project and organization"""
    try:
        # Get the admin user
        admin_user = User.objects.filter(email='admin@example.com').first()
        if not admin_user:
            print("❌ Admin user not found")
            return False
        
        print(f"Found admin user: {admin_user.email} (ID: {admin_user.id})")
        
        # Get the test project
        project_id = '93056c8a-c381-4da3-9eb5-471c917b8e83'
        project = Project.objects.filter(id=project_id).first()
        if not project:
            print(f"❌ Project with ID {project_id} not found")
            return False
            
        print(f"Found project: {project.name} (ID: {project.id})")
        print(f"Project organization: {project.organization.name} (ID: {project.organization.id})")
        
        # Add admin to organization if not already a member
        org_membership, org_created = OrganizationMember.objects.get_or_create(
            user=admin_user,
            organization=project.organization,
            defaults={'role': 'admin'}
        )
        
        if org_created:
            print(f"✅ Added admin to organization: {project.organization.name}")
        else:
            print(f"ℹ️ Admin already in organization: {project.organization.name}")
            
        # Add admin to project if not already a member
        project_membership, proj_created = ProjectMember.objects.get_or_create(
            user=admin_user,
            project=project,
            defaults={'role': 'owner'}
        )
        
        if proj_created:
            print(f"✅ Added admin to project: {project.name} with role 'owner'")
        else:
            print(f"ℹ️ Admin already in project: {project.name}")
            # Update role to owner if needed
            if not project_membership.is_owner:
                project_membership.role = ProjectMember.OWNER
                project_membership.save()
                print(f"✅ Updated admin's project role to 'owner'")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if add_admin_to_project():
        print("\n✅ Admin user successfully added to project and organization")
    else:
        print("\n❌ Failed to add admin user to project")
