from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from organizations.models import OrganizationMember
from .models import Project, ProjectMember, Board, Column
from .serializers import (
    ProjectSerializer, ProjectDetailSerializer,
    ProjectMemberSerializer, ProjectMemberCreateSerializer,
    BoardSerializer, ColumnSerializer
)
from .permissions import (
    IsProjectMember, IsProjectAdmin, IsProjectAdminOrReadOnly
)

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for projects
    """
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'organization']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'start_date', 'end_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Get all projects the user has access to
        # - Projects the user is a member of
        # - Public projects in organizations the user is a member of
        user = self.request.user
        
        # Get organizations the user is a member of
        user_orgs = OrganizationMember.objects.filter(user=user).values_list('organization_id', flat=True)
        
        return Project.objects.filter(
            # Projects the user is a member of
            Q(members__user=user) |
            # Public projects in organizations the user belongs to
            Q(organization_id__in=user_orgs, is_public=True)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsProjectAdmin]
        elif self.action in ['retrieve', 'list']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsProjectMember])
    def members(self, request, pk=None):
        """Get all members of a project"""
        project = self.get_object()
        members = ProjectMember.objects.filter(project=project)
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsProjectAdmin])
    def add_member(self, request, pk=None):
        """Add a member to a project"""
        project = self.get_object()
        
        serializer = ProjectMemberCreateSerializer(data={
            'project': project.id,
            'user': request.data.get('user'),
            'role': request.data.get('role', ProjectMember.MEMBER)
        })
        
        if serializer.is_valid():
            # Check if user is already a member
            user_id = serializer.validated_data.get('user').id
            if ProjectMember.objects.filter(project=project, user_id=user_id).exists():
                return Response(
                    {"detail": "User is already a member of this project."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Check if user is a member of the organization
            if not OrganizationMember.objects.filter(
                organization=project.organization,
                user_id=user_id
            ).exists():
                return Response(
                    {"detail": "User must be a member of the organization first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            member = serializer.save()
            return Response(ProjectMemberSerializer(member).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsProjectMember])
    def boards(self, request, pk=None):
        """Get all boards for a project"""
        project = self.get_object()
        boards = Board.objects.filter(project=project)
        serializer = BoardSerializer(boards, many=True)
        return Response(serializer.data)

class ProjectMemberViewSet(viewsets.ModelViewSet):
    """
    API endpoint for project members
    """
    serializer_class = ProjectMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        return ProjectMember.objects.filter(project_id=project_id)
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsProjectAdmin]
        return super().get_permissions()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Prevent removing the last owner
        if instance.role == ProjectMember.OWNER:
            # Check if this is the last owner
            owners_count = ProjectMember.objects.filter(
                project=instance.project,
                role=ProjectMember.OWNER
            ).count()
            
            if owners_count <= 1:
                return Response(
                    {"detail": "Cannot remove the last owner from the project."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return super().destroy(request, *args, **kwargs)

class BoardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for boards
    """
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        return Board.objects.filter(project_id=project_id)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsProjectAdmin]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, id=project_id)
        serializer.save(project=project, created_by=self.request.user)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsProjectMember])
    def columns(self, request, pk=None, project_pk=None):
        """Get all columns for a board"""
        board = self.get_object()
        columns = Column.objects.filter(board=board)
        serializer = ColumnSerializer(columns, many=True)
        return Response(serializer.data)

class ColumnViewSet(viewsets.ModelViewSet):
    """
    API endpoint for columns
    """
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        board_id = self.kwargs.get('board_pk')
        return Column.objects.filter(board_id=board_id)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsProjectAdminOrReadOnly]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        board_id = self.kwargs.get('board_pk')
        board = get_object_or_404(Board, id=board_id)
        
        # Set the order to be the last
        latest_column = Column.objects.filter(board=board).order_by('-order').first()
        next_order = (latest_column.order + 1) if latest_column else 0
        
        serializer.save(board=board, order=next_order)
