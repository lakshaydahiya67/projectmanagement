from rest_framework import permissions
from .models import OrganizationMember

class IsOrganizationMember(permissions.BasePermission):
    """
    Permission to only allow members of an organization to access it
    """
    def has_permission(self, request, view):
        organization_id = view.kwargs.get('organization_pk') or view.kwargs.get('pk')
        if not organization_id:
            return False
        
        return OrganizationMember.objects.filter(
            organization_id=organization_id,
            user=request.user
        ).exists()

class IsOrganizationAdmin(permissions.BasePermission):
    """
    Permission to only allow admins of an organization to modify it
    """
    def has_permission(self, request, view):
        organization_id = view.kwargs.get('organization_pk') or view.kwargs.get('pk')
        if not organization_id:
            return False
        
        membership = OrganizationMember.objects.filter(
            organization_id=organization_id,
            user=request.user
        ).first()
        
        if not membership:
            return False
        
        return membership.is_admin

class IsOrganizationManager(permissions.BasePermission):
    """
    Permission to only allow managers or admins of an organization to perform certain actions
    """
    def has_permission(self, request, view):
        organization_id = view.kwargs.get('organization_pk') or view.kwargs.get('pk')
        if not organization_id:
            return False
        
        membership = OrganizationMember.objects.filter(
            organization_id=organization_id,
            user=request.user
        ).first()
        
        if not membership:
            return False
        
        return membership.is_manager

class IsOrganizationAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow admins to make write actions
    Read permissions are allowed to any organization member
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any member
        if request.method in permissions.SAFE_METHODS:
            return IsOrganizationMember().has_permission(request, view)
        
        # Write permissions are only allowed to admins
        return IsOrganizationAdmin().has_permission(request, view)

class IsOrgMemberReadOnly(permissions.BasePermission):
    """
    Permission to allow read-only access to organization members.
    Used for resources that are accessible to any organization member but can't be modified.
    This is particularly useful for views like activity logs.
    """
    def has_permission(self, request, view):
        # Only allow read methods (GET, HEAD, OPTIONS)
        if request.method not in permissions.SAFE_METHODS:
            return False
            
        # For non-project specific views, check if user is a member of any organization
        if hasattr(request.user, 'memberships'):
            return request.user.memberships.exists()
            
        return False
        
    def has_object_permission(self, request, view, obj):
        # For object-level permissions (typically for retrieve, update, delete)
        # Check if user is a member of the organization this object belongs to
        # This assumes the object has a project_id field that links to a project
        if not hasattr(obj, 'project_id') or not obj.project_id:
            return False
            
        from projects.models import ProjectMember
        return ProjectMember.objects.filter(
            project_id=obj.project_id,
            user=request.user
        ).exists()
