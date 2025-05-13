from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django_filters.rest_framework import DjangoFilterBackend

from projects.models import Project, Column
from projects.permissions import IsProjectMember, IsProjectAdmin
from .models import Label, Task, Comment, Attachment
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

class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tasks
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['column', 'priority', 'assignees', 'labels']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'order']
    ordering = ['order']
    
    def get_queryset(self):
        column_id = self.kwargs.get('column_pk')
        return Task.objects.filter(column_id=column_id)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        column_id = self.kwargs.get('column_pk')
        column = get_object_or_404(Column, id=column_id)
        serializer.save(column=column)
    
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
            
            # Update task order and column
            task.column = new_column
            task.order = new_order
            task.save()
            
            # Reorder other tasks in the column
            if task.column_id == column_id:  # Same column
                Task.objects.filter(
                    column=task.column,
                    order__gte=new_order
                ).exclude(id=task.id).update(order=F('order') + 1)
            
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
            
            # Clear existing assignees and add new ones
            task.assignees.clear()
            task.assignees.add(*valid_members)
            
            # TODO: Create notifications for newly assigned users
            
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
        
        return Response(TaskDetailSerializer(task).data)
    
    @action(detail=True, methods=['post'])
    def remove_labels(self, request, pk=None, column_pk=None):
        """Remove labels from a task"""
        task = self.get_object()
        label_ids = request.data.get('label_ids', [])
        
        # Remove labels from the task
        task.labels.remove(*label_ids)
        
        return Response(TaskDetailSerializer(task).data)

class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task comments
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        return Comment.objects.filter(task_id=task_id)
    
    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk')
        task = get_object_or_404(Task, id=task_id)
        serializer.save(task=task)
    
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
        serializer.save(task=task)
    
    def get_permissions(self):
        if self.action in ['destroy']:
            # Only attachment uploader or project admin can delete
            self.permission_classes = [permissions.IsAuthenticated, IsAttachmentUploaderOrProjectAdmin]
        return super().get_permissions()

# Custom permissions for comments and attachments
class IsCommentAuthor(permissions.BasePermission):
    """Permission to only allow authors of a comment to edit it"""
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user

class IsAttachmentUploaderOrProjectAdmin(permissions.BasePermission):
    """Permission to only allow uploaders or project admins to delete attachments"""
    def has_object_permission(self, request, view, obj):
        # Allow if user is the uploader
        if obj.uploaded_by == request.user:
            return True
        
        # Allow if user is a project admin
        project = obj.task.column.board.project
        return project.members.filter(
            user=request.user, 
            role__in=[ProjectMember.ADMIN, ProjectMember.OWNER]
        ).exists()
