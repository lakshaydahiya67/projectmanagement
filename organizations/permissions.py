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
