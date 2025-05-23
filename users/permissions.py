from rest_framework import permissions
import re

class AllowPasswordReset(permissions.BasePermission):
    """
    Permission class that allows unauthenticated access to password reset endpoints
    """
    def has_permission(self, request, view):
        # Check if the path is a password reset endpoint
        path = request.path
        if (path.endswith('/password-reset/') or 
            'reset_password' in path or 
            'forgot-password' in path):
            return True
        
        # For other endpoints, defer to the default permission classes
        return request.user and request.user.is_authenticated

class IsUserOwner(permissions.BasePermission):
    """
    Permission to only allow users to edit their own profile
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the user itself
        return obj == request.user

class IsUserOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow users to edit their own user-related objects
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the object's owner
        return obj.user == request.user
