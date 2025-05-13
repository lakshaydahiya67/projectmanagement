from rest_framework import permissions
from .models import ProjectMember, Project
from organizations.models import OrganizationMember

class IsProjectMember(permissions.BasePermission):
    """
    Permission to only allow members of a project to access it
    """
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_pk') or view.kwargs.get('pk')
        if not project_id:
            return False
        
        # Check if project is public
        try:
            project = Project.objects.get(id=project_id)
            if project.is_public:
                # For public projects, check if user is in the organization
                return OrganizationMember.objects.filter(
                    organization=project.organization,
                    user=request.user
                ).exists()
        except Project.DoesNotExist:
            return False
        
        # For private projects, check project membership
        return ProjectMember.objects.filter(
            project_id=project_id,
            user=request.user
        ).exists()
    
    def has_object_permission(self, request, view, obj):
        # Check if project field exists on the object
        if hasattr(obj, 'project'):
            project = obj.project
        elif isinstance(obj, Project):
            project = obj
        else:
            return False
            
        if project.is_public:
            # For public projects, check if user is in the organization
            return OrganizationMember.objects.filter(
                organization=project.organization,
                user=request.user
            ).exists()
            
        # For private projects, check project membership
        return ProjectMember.objects.filter(
            project=project,
            user=request.user
        ).exists()

class IsProjectAdmin(permissions.BasePermission):
    """
    Permission to only allow admins/owners of a project to modify it
    """
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_pk') or view.kwargs.get('pk')
        if not project_id:
            return False
        
        membership = ProjectMember.objects.filter(
            project_id=project_id,
            user=request.user
        ).first()
        
        if not membership:
            return False
        
        return membership.is_admin
    
    def has_object_permission(self, request, view, obj):
        # Check if project field exists on the object
        if hasattr(obj, 'project'):
            project = obj.project
        elif isinstance(obj, Project):
            project = obj
        else:
            return False
        
        membership = ProjectMember.objects.filter(
            project=project,
            user=request.user
        ).first()
        
        if not membership:
            return False
        
        return membership.is_admin

class IsProjectAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow admins to make write actions
    Read permissions are allowed to any project member
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any member
        if request.method in permissions.SAFE_METHODS:
            return IsProjectMember().has_permission(request, view)
        
        # Write permissions are only allowed to admins
        return IsProjectAdmin().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any member
        if request.method in permissions.SAFE_METHODS:
            return IsProjectMember().has_object_permission(request, view, obj)
        
        # Write permissions are only allowed to admins
        return IsProjectAdmin().has_object_permission(request, view, obj)
