from rest_framework import permissions

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
