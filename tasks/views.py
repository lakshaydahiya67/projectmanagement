from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle
from django.shortcuts import get_object_or_404, render
from django.db.models import Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
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
        
        # Send real-time update via WebSocket
        channel_layer = get_channel_layer()
        
        # Serialize task for WebSocket
        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'order': task.order,
            'priority': task.priority,
            'priority_display': task.get_priority_display(),
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'created_by': {
                'id': self.request.user.id,
                'username': self.request.user.username,
                'full_name': self.request.user.get_full_name(),
                'avatar': self.request.user.profile_picture.url if self.request.user.profile_picture else None
            }
        }
        
        # Send to board group
        board_group_name = f'board_{column.board.id}'
        async_to_sync(channel_layer.group_send)(
            board_group_name,
            {
                'type': 'task_create_message',
                'task': task_data,
                'column_id': column.id,
                'user': {
                    'id': self.request.user.id,
                    'username': self.request.user.username,
                    'full_name': self.request.user.get_full_name(),
                    'avatar': self.request.user.profile_picture.url if self.request.user.profile_picture else None
                }
            }
        )
    
    @action(detail=False, methods=['post'])
    def filter_tasks(self, request, column_pk=None):
        """
        Advanced task filtering with multiple conditions
        """
        # Get base queryset from the column
        column = get_object_or_404(Column, id=column_pk)
        queryset = Task.objects.filter(column=column)
        
        # Filter by date range if provided
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
        
        # Filter by due date
        due_before = request.data.get('due_before')
        due_after = request.data.get('due_after')
        
        if due_before:
            queryset = queryset.filter(due_date__lte=due_before)
        
        if due_after:
            queryset = queryset.filter(due_date__gte=due_after)
            
        # Filter by overdue status
        overdue = request.data.get('overdue')
        if overdue:
            queryset = queryset.filter(
                due_date__lt=timezone.now()
            )
            
        # Filter by priority
        priorities = request.data.get('priorities')
        if priorities:
            queryset = queryset.filter(priority__in=priorities)
            
        # Filter by label
        labels = request.data.get('labels')
        if labels:
            queryset = queryset.filter(labels__id__in=labels)
            
        # Filter by assignee
        assignees = request.data.get('assignees')
        if assignees:
            queryset = queryset.filter(assignees__id__in=assignees)
            
        # Filter by unassigned
        unassigned = request.data.get('unassigned')
        if unassigned:
            queryset = queryset.filter(assignees__isnull=True)
            
        # Filter by search term
        search = request.data.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
            
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = TaskSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None, column_pk=None):
        """Move a task to another column or change its order"""
        task = self.get_object()
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
            
            # Send real-time update via WebSocket
            channel_layer = get_channel_layer()
            
            # Send to board group
            board_group_name = f'board_{task.column.board.id}'
            async_to_sync(channel_layer.group_send)(
                board_group_name,
                {
                    'type': 'task_move_message',
                    'task_id': task.id,
                    'source_column_id': old_column_id,
                    'destination_column_id': new_column.id,
                    'order': new_order,
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'full_name': request.user.get_full_name(),
                        'avatar': request.user.profile_picture.url if request.user.profile_picture else None
                    }
                }
            )
            
            return Response(TaskSerializer(task).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None, column_pk=None):
        """Assign users to a task"""
        task = self.get_object()
        serializer = TaskAssignSerializer(data=request.data)
        
        if serializer.is_valid():
            user_ids = serializer.validated_data.get('user_ids')
            
            # Validate all users are members of the project
            project = task.column.board.project
            valid_members = project.members.filter(user_id__in=user_ids).values_list('user_id', flat=True)
            
            if len(valid_members) != len(user_ids):
                invalid_ids = set(user_ids) - set(valid_members)
                return Response(
                    {"detail": f"Users with IDs {invalid_ids} are not members of this project."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get list of previous assignees before clearing
            previous_assignees = set(task.assignees.values_list('id', flat=True))
            
            # Clear existing assignees and add new ones
            task.assignees.clear()
            task.assignees.add(*valid_members)
            
            # Create notifications for newly assigned users
            if NOTIFICATIONS_AVAILABLE:
                for user_id in valid_members:
                    # Only create notifications for newly assigned users
                    if user_id not in previous_assignees:
                        send_task_assigned_notification(
                            task_id=task.id,
                            user_id=user_id,
                            assigned_by_id=request.user.id
                        )
            
            # Send WebSocket notification for task assignment
            channel_layer = get_channel_layer()
            
            # Send to project group
            project_group_name = f'project_{project.id}'
            async_to_sync(channel_layer.group_send)(
                project_group_name,
                {
                    'type': 'task_update_message',
                    'task_id': task.id,
                    'updates': {
                        'assignees': [
                            {
                                'id': user_id,
                                'username': User.objects.get(id=user_id).username,
                                'full_name': User.objects.get(id=user_id).get_full_name()
                            } for user_id in valid_members
                        ]
                    },
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'full_name': request.user.get_full_name(),
                        'avatar': request.user.profile_picture.url if request.user.profile_picture else None
                    }
                }
            )
            
            return Response(TaskDetailSerializer(task).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_labels(self, request, pk=None, column_pk=None):
        """Add labels to a task"""
        task = self.get_object()
        label_ids = request.data.get('label_ids', [])
        
        # Validate all labels belong to the project
        project = task.column.board.project
        valid_labels = Label.objects.filter(
            id__in=label_ids,
            project=project
        ).values_list('id', flat=True)
        
        if len(valid_labels) != len(label_ids):
            invalid_ids = set(label_ids) - set(valid_labels)
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
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        
        # Get labels for the response
        labels_data = [
            {
                'id': label.id,
                'name': label.name,
                'color': label.color
            }
            for label in Label.objects.filter(id__in=valid_labels)
        ]
        
        # Send to board group
        board_group_name = f'board_{task.column.board.id}'
        async_to_sync(channel_layer.group_send)(
            board_group_name,
            {
                'type': 'task_label_message',
                'task_id': task.id,
                'labels': labels_data,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'full_name': request.user.get_full_name(),
                    'avatar': request.user.profile_picture.url if request.user.profile_picture else None
                }
            }
        )
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        
        # Get updated labels
        label_data = [
            {
                'id': label.id,
                'name': label.name,
                'color': label.color
            } for label in task.labels.all()
        ]
        
        # Send to project group
        project_group_name = f'project_{task.column.board.project.id}'
        async_to_sync(channel_layer.group_send)(
            project_group_name,
            {
                'type': 'task_update_message',
                'task_id': task.id,
                'updates': {
                    'labels': label_data
                },
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'full_name': request.user.get_full_name(),
                    'avatar': request.user.profile_picture.url if request.user.profile_picture else None
                }
            }
        )
        
        return Response(TaskDetailSerializer(task).data)
    
    @action(detail=True, methods=['post'])
    def remove_labels(self, request, pk=None, column_pk=None):
        """Remove labels from a task"""
        task = self.get_object()
        label_ids = request.data.get('label_ids', [])
        
        # Validate labels exist in the project first
        project = task.column.board.project
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
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        
        # Get updated labels
        label_data = [
            {
                'id': label.id,
                'name': label.name,
                'color': label.color
            } for label in task.labels.all()
        ]
        
        # Send to board group
        board_group_name = f'board_{task.column.board.id}'
        async_to_sync(channel_layer.group_send)(
            board_group_name,
            {
                'type': 'task_label_message',
                'task_id': task.id,
                'labels': label_data,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'full_name': request.user.get_full_name(),
                    'avatar': request.user.profile_picture.url if request.user.profile_picture else None
                }
            }
        )
        
        return Response(TaskDetailSerializer(task).data)

class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task comments
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    throttle_classes = [CommentRateThrottle]
    
    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        return Comment.objects.filter(task_id=task_id)
    
    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk')
        task = get_object_or_404(Task, id=task_id)
        comment = serializer.save(task=task, author=self.request.user)
        
        # Log activity
        if ACTIVITYLOG_AVAILABLE:
            ActivityLog.objects.create(
                user=self.request.user,
                content_type=ContentType.objects.get_for_model(task),
                object_id=str(task.id),
                action_type=ActivityLog.COMMENTED,
                description=f"Commented on task '{task.title}'"
            )
        
        # Check for @mentions in comment content
        import re
        mentions = re.findall(r'@(\w+)', comment.content)
        if mentions:
            # Get mentioned users who are project members
            project = task.column.board.project
            mentioned_users = User.objects.filter(
                username__in=mentions,
                project_memberships__project=project
            )
            
            # Create mention notifications
            from notifications.models import Notification
            from django.contrib.contenttypes.models import ContentType
            
            task_content_type = ContentType.objects.get_for_model(Task)
            for user in mentioned_users:
                if user != self.request.user:  # Don't notify the commenter about their own mentions
                    Notification.objects.create(
                        recipient=user,
                        notification_type=Notification.MENTIONED,
                        title=f"You were mentioned in a comment",
                        message=f"{self.request.user.get_full_name()} mentioned you in a comment on task '{task.title}'",
                        content_type=task_content_type,
                        object_id=task.id
                    )
        
        # Send notification
        if NOTIFICATIONS_AVAILABLE:
            send_comment_notification(comment_id=comment.id)
        
        # Send real-time WebSocket update
        channel_layer = get_channel_layer()
        
        # Serialize comment for WebSocket
        comment_data = {
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'author': {
                'id': comment.author.id,
                'username': comment.author.username,
                'full_name': comment.author.get_full_name(),
                'avatar': comment.author.profile_picture.url if comment.author.profile_picture else None
            },
            'parent_id': comment.parent_id
        }
        
        # Send to project group for any users viewing the project
        project_group_name = f'project_{task.column.board.project.id}'
        async_to_sync(channel_layer.group_send)(
            project_group_name,
            {
                'type': 'comment_add_message',
                'task_id': task.id,
                'comment': comment_data,
                'user': {
                    'id': self.request.user.id,
                    'username': self.request.user.username,
                    'full_name': self.request.user.get_full_name(),
                    'avatar': self.request.user.profile_picture.url if self.request.user.profile_picture else None
                }
            }
        )
        
        return comment
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only comment author can edit or delete
            self.permission_classes = [permissions.IsAuthenticated, IsCommentAuthor]
        return super().get_permissions()

class AttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task attachments
    """
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        return Attachment.objects.filter(task_id=task_id)
    
    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk')
        task = get_object_or_404(Task, id=task_id)
        attachment = serializer.save(task=task, uploaded_by=self.request.user)
        
        # Log activity
        if ACTIVITYLOG_AVAILABLE:
            ActivityLog.objects.create(
                user=self.request.user,
                content_type=ContentType.objects.get_for_model(task),
                object_id=str(task.id),
                action_type=ActivityLog.CREATED,
                description=f"Added attachment '{attachment.filename}' to task"
            )
    
    def get_permissions(self):
        if self.action in ['destroy']:
            # Only attachment uploader or project admin can delete
            self.permission_classes = [permissions.IsAuthenticated, IsAttachmentUploaderOrProjectAdmin]
        return super().get_permissions()

# Custom permissions for comments and attachments
class IsCommentAuthor(permissions.BasePermission):
    """
    Permission that allows only the comment author to modify/delete it
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the comment author
        return obj.author == request.user

class IsAttachmentUploaderOrProjectAdmin(permissions.BasePermission):
    """
    Permission that allows only the attachment uploader or project admin to delete it
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is the uploader
        if obj.uploaded_by == request.user:
            return True
        
        # Check if user is a project admin
        task = obj.task
        project = task.column.board.project
        return ProjectMember.objects.filter(
            project=project,
            user=request.user,
            role__in=[ProjectMember.ADMIN, ProjectMember.OWNER]
        ).exists()


# View for rendering the task detail HTML page
def task_detail_view(request, task_id, project_id=None):
    """
    View function for rendering the task detail page with task object in context
    Can be accessed with or without project_id in the URL
    """
    task = get_object_or_404(Task, id=task_id)
    project = task.column.board.project
    
    # Verify project_id if provided
    if project_id and str(project.id) != str(project_id):
        return render(request, 'base/error.html', {
            'message': 'Task does not belong to the specified project.'
        }, status=400)
    
    # Permission check: user must be a member of the project or the project must be public
    is_member = ProjectMember.objects.filter(project=project, user=request.user).exists()
    
    if not (is_member or request.user.is_staff):
        return render(request, 'base/error.html', {
            'message': 'You do not have permission to view this task.'
        }, status=403)
    
    # Add task and related objects to context
    context = {
        'task': task,
        'project': project,
        'column': task.column,
        'board': task.column.board
    }
    
    return render(request, 'task/task_detail.html', context)


# View for rendering the task creation HTML page
def task_create_view(request, project_id):
    """
    View function for rendering the task creation page
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Permission check: user must be a member of the project
    is_member = ProjectMember.objects.filter(project=project, user=request.user).exists()
    
    if not (is_member or request.user.is_staff):
        return render(request, 'base/error.html', {
            'message': 'You do not have permission to create tasks in this project.'
        }, status=403)
    
    # Get the boards for this project
    boards = project.boards.all()
    
    # Get all columns from all boards
    columns = Column.objects.filter(board__in=boards)
    
    # Get project members for assignee selection
    project_members = ProjectMember.objects.filter(project=project)
    
    # Get labels for this project
    labels = Label.objects.filter(project=project)
    
    context = {
        'project': project,
        'boards': boards,
        'columns': columns,
        'project_members': project_members,
        'labels': labels
    }
    
    return render(request, 'task/task_create.html', context)


# View for rendering the task update HTML page
def task_update_view(request, task_id, project_id=None):
    """
    View function for rendering the task update page
    Can be accessed with or without project_id in the URL
    """
    task = get_object_or_404(Task, id=task_id)
    project = task.column.board.project
    
    # Verify project_id if provided
    if project_id and str(project.id) != str(project_id):
        return render(request, 'base/error.html', {
            'message': 'Task does not belong to the specified project.'
        }, status=400)
    
    # Permission check: user must be a member of the project
    is_member = ProjectMember.objects.filter(project=project, user=request.user).exists()
    
    if not (is_member or request.user.is_staff):
        return render(request, 'base/error.html', {
            'message': 'You do not have permission to update this task.'
        }, status=403)
    
    # Get the boards for this project
    boards = project.boards.all()
    
    # Get all columns from all boards
    columns = Column.objects.filter(board__in=boards)
    
    # Get project members for assignee selection
    project_members = ProjectMember.objects.filter(project=project)
    
    # Get labels for this project
    labels = Label.objects.filter(project=project)
    
    context = {
        'task': task,
        'project': project,
        'boards': boards,
        'columns': columns,
        'project_members': project_members,
        'labels': labels,
        'board': task.column.board
    }
    
    return render(request, 'task/task_update.html', context)
