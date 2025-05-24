from rest_framework import permissions
from .models import ProjectMember, Project
from organizations.models import OrganizationMember

class IsProjectMember(permissions.BasePermission):
    """
    Permission to only allow members of a project to access it
    """
    def has_permission(self, request, view):
        # Try to get project ID from various possible routes
        project_id = view.kwargs.get('project_pk') or view.kwargs.get('pk')
        
        # Handle nested routes through columns
        if not project_id:
            column_id = view.kwargs.get('column_pk')
            if column_id:
                from projects.models import Column
                try:
                    column = Column.objects.get(id=column_id)
                    project_id = column.board.project_id
                except Column.DoesNotExist:
                    return False
            else:
                # For task creation via /api/v1/tasks/, get project from column in request data
                if hasattr(request, 'data') and 'column' in request.data:
                    column_id = request.data.get('column')
                    if column_id:
                        from projects.models import Column
                        try:
                            column = Column.objects.get(id=column_id)
                            project_id = column.board.project_id
                        except Column.DoesNotExist:
                            return False
                    else:
                        return False
                else:
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
        elif hasattr(obj, 'column') and hasattr(obj.column, 'board'):
            # Support for Task objects that have column->board->project path
            project = obj.column.board.project
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
        # Try to get project ID from various possible routes
        project_id = view.kwargs.get('project_pk') or view.kwargs.get('pk')
        
        # Handle nested routes through columns
        if not project_id:
            column_id = view.kwargs.get('column_pk')
            if column_id:
                from projects.models import Column
                try:
                    column = Column.objects.get(id=column_id)
                    project_id = column.board.project_id
                except Column.DoesNotExist:
                    return False
            else:
                # For task creation via /api/v1/tasks/, get project from column in request data
                if hasattr(request, 'data') and 'column' in request.data:
                    column_id = request.data.get('column')
                    if column_id:
                        from projects.models import Column
                        try:
                            column = Column.objects.get(id=column_id)
                            project_id = column.board.project_id
                        except Column.DoesNotExist:
                            return False
                    else:
                        return False
                else:
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
        elif hasattr(obj, 'column') and hasattr(obj.column, 'board'):
            # Support for Task objects that have column->board->project path
            project = obj.column.board.project
        else:
            return False
        
        membership = ProjectMember.objects.filter(
            project=project,
            user=request.user
        ).first()
        
        if not membership:
            return False
        
        return membership.is_admin

class IsProjectManager(permissions.BasePermission):
    """
    Permission to only allow managers, admins, or owners of a project to perform certain actions
    """
    def has_permission(self, request, view):
        # Try to get project ID from various possible routes
        project_id = view.kwargs.get('project_pk') or view.kwargs.get('pk')
        
        # Handle nested routes through columns
        if not project_id:
            column_id = view.kwargs.get('column_pk')
            if column_id:
                from projects.models import Column
                try:
                    column = Column.objects.get(id=column_id)
                    project_id = column.board.project_id
                except Column.DoesNotExist:
                    return False
            else:
                return False
        
        membership = ProjectMember.objects.filter(
            project_id=project_id,
            user=request.user
        ).first()
        
        if not membership:
            return False
        
        return membership.is_manager
    
    def has_object_permission(self, request, view, obj):
        # Check if project field exists on the object
        if hasattr(obj, 'project'):
            project = obj.project
        elif isinstance(obj, Project):
            project = obj
        elif hasattr(obj, 'column') and hasattr(obj.column, 'board'):
            # Support for Task objects that have column->board->project path
            project = obj.column.board.project
        else:
            return False
        
        membership = ProjectMember.objects.filter(
            project=project,
            user=request.user
        ).first()
        
        if not membership:
            return False
        
        return membership.is_manager

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
