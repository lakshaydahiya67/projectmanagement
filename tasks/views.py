from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle
from django.shortcuts import get_object_or_404, render
from django.db.models import Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
# WebSocket functionality removed
from django.contrib.contenttypes.models import ContentType

from projects.models import Project, Column, ProjectMember
from projects.permissions import IsProjectMember, IsProjectAdmin
from .models import Label, Task, Comment, Attachment
from django.contrib.auth import get_user_model

# Get ActivityLog model if available
try:
    from activitylogs.models import ActivityLog
    ACTIVITYLOG_AVAILABLE = True
except ImportError:
    ACTIVITYLOG_AVAILABLE = False

# Try to import notification utils if available
try:
    from notifications.utils import send_task_assigned_notification, send_comment_notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

User = get_user_model()

# WebSocket functionality removed
from .serializers import (
    LabelSerializer, TaskSerializer, TaskDetailSerializer, 
    CommentSerializer, AttachmentSerializer,
    TaskMoveSerializer, TaskAssignSerializer
)

class LabelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task labels
    """
    serializer_class = LabelSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        return Label.objects.filter(project_id=project_id)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsProjectAdmin]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, id=project_id)
        serializer.save(project=project)

class CreateTaskRateThrottle(ScopedRateThrottle):
    scope = 'create_task'

class UpdateTaskRateThrottle(ScopedRateThrottle):
    scope = 'update_task'

class CommentRateThrottle(ScopedRateThrottle):
    scope = 'comments'

class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tasks
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    queryset = Task.objects.all()  # Default queryset for router registration
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['column', 'priority', 'assignees', 'labels']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'order']
    ordering = ['order']
    throttle_classes = [UserRateThrottle]
    
    def _check_task_permission(self, task, user, require_admin=False):
        """
        Helper method to check if a user has permission to access a task
        Returns (project, is_member, is_admin, response_on_error)
        If permission check passes, response_on_error will be None
        If permission check fails, response_on_error will be a Response object
        """
        project = task.column.board.project
        
        # Check if user is project member
        member = ProjectMember.objects.filter(
            project=project,
            user=user
        ).first()
        
        is_member = member is not None
        is_admin = is_member and member.role in ['admin', 'owner']
        
        if not is_member:
            error_response = Response(
                {"detail": "You do not have permission to access this task."},
                status=status.HTTP_403_FORBIDDEN
            )
            return project, is_member, is_admin, error_response
            
        if require_admin and not is_admin:
            error_response = Response(
                {"detail": "You must be a project admin to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
            return project, is_member, is_admin, error_response
            
        return project, is_member, is_admin, None
    
    def get_queryset(self):
        # Check if this is a schema generation request for Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()
            
        # Get project_pk from URL parameters
        project_pk = self.kwargs.get('project_pk')
        if project_pk:
            # If we're accessing tasks for a specific project
            return Task.objects.filter(
                column__board__project_id=project_pk
            ).select_related('column', 'column__board').prefetch_related('labels', 'assignees')
        
        # Get column_pk from URL parameters (for nested routes)
        column_pk = self.kwargs.get('column_pk')
        if column_pk:
            # If we're accessing tasks for a specific column
            return Task.objects.filter(
                column_id=column_pk
            ).select_related('column', 'column__board').prefetch_related('labels', 'assignees')
            
        # If no specific filters in URL, return tasks the user has access to
        user = self.request.user
        return Task.objects.filter(
            column__board__project__members__user=user
        ).select_related('column', 'column__board').prefetch_related('labels', 'assignees').distinct()
        
    def list(self, request, *args, **kwargs):
        """
        Override list method to handle pagination properly for frontend compatibility
        When called from project detail view, we need to return a direct array for tasks.forEach
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Check if pagination is explicitly requested
        paginate = request.query_params.get('paginate', 'false').lower() == 'true'
        
        if paginate:
            # Use normal pagination behavior
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        
        # Otherwise return direct array response for frontend compatibility
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path=r'(?P<task_id>[^/.]+)/assign_task')
    def assign_task(self, request, column_pk=None, task_id=None):
        """
        Custom action to assign users to a task
        """
        task = get_object_or_404(Task, id=task_id, column_id=column_pk)
        
        # Check permissions using helper method
        project, is_member, is_admin, error_response = self._check_task_permission(task, request.user)
        if error_response:
            return error_response
        
        user_ids = request.data.get('user_ids', [])
        
        # Validate all users are members of the project
        valid_members = ProjectMember.objects.filter(
            project=project,
            user_id__in=user_ids
        ).values_list('user_id', flat=True)
        
        if len(valid_members) != len(user_ids):
            invalid_ids = set(user_ids) - set(str(id) for id in valid_members)
            return Response(
                {"detail": f"Users with IDs {invalid_ids} are not members of this project."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get list of previous assignees before clearing
        previous_assignees = set(task.assignees.values_list('id', flat=True))
        
        # Clear existing assignees and add new ones
        task.assignees.clear()
        task.assignees.add(*valid_members)
        
        # Log activity
        if ACTIVITYLOG_AVAILABLE:
            ActivityLog.objects.create(
                user=request.user,
                content_type=ContentType.objects.get_for_model(task),
                object_id=str(task.id),
                action_type=ActivityLog.UPDATED,
                description=f"Updated task assignees"
            )
        
        return Response(TaskDetailSerializer(task).data)
    
    @action(detail=False, methods=['post'], url_path=r'(?P<task_id>[^/.]+)/remove_labels_task')
    def remove_labels_task(self, request, column_pk=None, task_id=None):
        """
        Custom action to remove labels from a task
        """
        task = get_object_or_404(Task, id=task_id, column_id=column_pk)
        
        # Check permissions using helper method
        project, is_member, is_admin, error_response = self._check_task_permission(task, request.user)
        if error_response:
            return error_response
        
        label_ids = request.data.get('label_ids', [])
        
        # Validate labels exist in the project first
        valid_labels = Label.objects.filter(
            id__in=label_ids,
            project=project
        ).values_list('id', flat=True)
        
        # Remove labels from the task
        task.labels.remove(*valid_labels)
        
        # Log activity
        if ACTIVITYLOG_AVAILABLE:
            ActivityLog.objects.create(
                user=request.user,
                content_type=ContentType.objects.get_for_model(task),
                object_id=str(task.id),
                action_type=ActivityLog.UPDATED,
                description=f"Removed labels from task"
            )
        
        return Response(TaskDetailSerializer(task).data)
    
    @action(detail=False, methods=['post'], url_path=r'(?P<task_id>[^/.]+)/add_labels_task')
    def add_labels_task(self, request, column_pk=None, task_id=None):
        """
        Custom action to add labels to a task
        """
        task = get_object_or_404(Task, id=task_id, column_id=column_pk)
        
        # Check permissions using helper method
        project, is_member, is_admin, error_response = self._check_task_permission(task, request.user)
        if error_response:
            return error_response
        
        label_ids = request.data.get('label_ids', [])
        
        # Validate all labels belong to the project
        valid_labels = Label.objects.filter(
            id__in=label_ids,
            project=project
        ).values_list('id', flat=True)
        
        if len(valid_labels) != len(label_ids):
            invalid_ids = set(label_ids) - set(str(id) for id in valid_labels)
            return Response(
                {"detail": f"Labels with IDs {invalid_ids} do not exist or don't belong to this project."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add labels to the task
        task.labels.add(*valid_labels)
        
        # Log activity
        if ACTIVITYLOG_AVAILABLE:
            ActivityLog.objects.create(
                user=request.user,
                content_type=ContentType.objects.get_for_model(task),
                object_id=str(task.id),
                action_type=ActivityLog.UPDATED,
                description=f"Added labels to task"
            )
        
        return Response(TaskDetailSerializer(task).data)
    
    @action(detail=False, methods=['post'], url_path=r'(?P<task_id>[^/.]+)/move_task')
    def move_task(self, request, column_pk=None, task_id=None):
        """
        Custom action to move a task between columns
        """
        task = get_object_or_404(Task, id=task_id, column_id=column_pk)
        
        # Check permissions using helper method
        project, is_member, is_admin, error_response = self._check_task_permission(task, request.user)
        if error_response:
            return error_response
        
        serializer = TaskMoveSerializer(data=request.data)
        
        if serializer.is_valid():
            column_id = serializer.validated_data.get('column')
            new_order = serializer.validated_data.get('order')
            
            # Validate column exists and is in the same project
            try:
                new_column = Column.objects.get(
                    id=column_id,
                    board__project=task.column.board.project
                )
            except Column.DoesNotExist:
                return Response(
                    {"detail": "Column not found or not in the same project."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            old_column_id = task.column_id
            
            # Update task order and column
            task.column = new_column
            task.order = new_order
            task.save()
            
            # Reorder other tasks in the destination column
            Task.objects.filter(
                column_id=column_id,
                order__gte=new_order
            ).exclude(id=task.id).update(order=F('order') + 1)
            
            # If moving between columns, compact the order in the source column
            if old_column_id != column_id:
                # Get all tasks in the old column and reorder them sequentially
                old_column_tasks = Task.objects.filter(column_id=old_column_id).order_by('order')
                for i, t in enumerate(old_column_tasks):
                    if t.order != i:
                        t.order = i
                        t.save(update_fields=['order'])
            
            # Log activity
            if ACTIVITYLOG_AVAILABLE:
                ActivityLog.objects.create(
                    user=request.user,
                    content_type=ContentType.objects.get_for_model(task),
                    object_id=str(task.id),
                    action_type=ActivityLog.UPDATED,
                    description=f"Moved task '{task.title}' to column '{new_column.name}'"
                )
            
            return Response(TaskSerializer(task).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get', 'put', 'patch', 'delete'], url_path=r'(?P<task_id>[^/.]+)/details')
    def task_details(self, request, column_pk=None, task_id=None):
        """
        Custom action to get, update, or delete task details to bypass complex permission checks
        """
        task = get_object_or_404(Task, id=task_id, column_id=column_pk)
        
        # Manually check if user has permission
        project = task.column.board.project
        
        # Check if user is project member
        is_member = ProjectMember.objects.filter(
            project=project,
            user=request.user
        ).exists()
        
        if not is_member:
            return Response(
                {"detail": "You do not have permission to access this task."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            serializer = TaskDetailSerializer(task)
            return Response(serializer.data)
        elif request.method in ['PUT', 'PATCH']:
            serializer = TaskSerializer(task, data=request.data, partial=request.method == 'PATCH')
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()
            
        # Handle case where kwargs is not set (during routing inspection)
        # This is critical for Django REST Framework router registration
        if not hasattr(self, 'kwargs'):
            return self.queryset
            
        # Handle case where request is not available (during introspection)
        if not hasattr(self, 'request'):
            return self.queryset
            
        # Safety check to prevent any attribute errors during routing inspection
        try:
            # Check if this is a direct route or a nested route
            column_id = self.kwargs.get('column_pk')
            task_id = self.kwargs.get('pk') or self.kwargs.get('task_id')
            
            # If we have a specific task ID and no column ID, return just that task
            if task_id and not column_id:
                return Task.objects.filter(id=task_id)
            
            # If we have a column ID, filter by column
            if column_id:
                return Task.objects.filter(column_id=column_id)
                
            # Default case: return all tasks the user has access to
            # Get all projects the user is a member of
            if hasattr(self.request, 'user') and self.request.user.is_authenticated:
                user_projects = Project.objects.filter(
                    members__user=self.request.user
                )
                
                # Return all tasks in columns that belong to boards in those projects
                return Task.objects.filter(
                    column__board__project__in=user_projects
                )
            else:
                # Fallback for unauthenticated requests
                return self.queryset
        except (AttributeError, KeyError, TypeError):
            # Catch any unexpected errors during routing inspection
            return self.queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer
        
    def get_throttles(self):
        """
        Apply different throttling rates based on the action
        """
        if self.action == 'create':
            self.throttle_scope = 'create_task'
            return [CreateTaskRateThrottle()]
        elif self.action in ['update', 'partial_update', 'move', 'add_labels', 'remove_labels']:
            self.throttle_scope = 'update_task'
            return [UpdateTaskRateThrottle()]
        return [UserRateThrottle()]
    
    def perform_create(self, serializer):
        column_id = self.kwargs.get('column_pk')
        
        # Direct route case - column should be provided in the request data
        if not column_id:
            column = serializer.validated_data.get('column')
            if not column:
                raise serializers.ValidationError({"column": "Column ID is required"})
            # column is already a Column object from PrimaryKeyRelatedField
        else:
            # Nested route case
            column = get_object_or_404(Column, id=column_id)
        
        # Verify the user has access to this column's project
        project = column.board.project
        if not ProjectMember.objects.filter(project=project, user=self.request.user).exists():
            raise permissions.PermissionDenied("You do not have permission to create tasks in this column.")
        
        task = serializer.save(column=column, created_by=self.request.user)
        
        # Log activity
        if ACTIVITYLOG_AVAILABLE:
            ActivityLog.objects.create(
                user=self.request.user,
                content_type=ContentType.objects.get_for_model(task),
                object_id=str(task.id),
                action_type=ActivityLog.CREATED,
                description=f"Created task '{task.title}' in column '{column.name}'"
            )


# Template-based views for non-API access
def task_detail_view(request, task_id, project_id=None):
    """Display task details"""
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'tasks/task_detail.html', {'task': task})


def task_create_view(request, project_id):
    """Create a new task"""
    project = get_object_or_404(Project, id=project_id)
    return render(request, 'tasks/task_create.html', {'project': project})


def task_update_view(request, task_id, project_id):
    """Update a task"""
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'tasks/task_update.html', {'task': task})


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing task comments"""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        return Comment.objects.all()

    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk')
        task = get_object_or_404(Task, id=task_id)
        serializer.save(task=task, author=self.request.user)


class AttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing task attachments"""
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        return Attachment.objects.all()

    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk')
        task = get_object_or_404(Task, id=task_id)
        serializer.save(task=task, uploaded_by=self.request.user)
