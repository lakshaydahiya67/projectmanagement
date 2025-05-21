from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render, redirect
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
    queryset = Project.objects.all()  # Add this line to fix the router issue
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'organization']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'start_date', 'end_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Check if this is a schema generation request for Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Project.objects.none()
            
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

# View for rendering the project detail HTML page
def project_detail_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user = request.user

    # Permission check: 
    # 1. User is a member of the project OR
    # 2. Project is public AND user is a member of the project's organization OR
    # 3. User is staff
    is_member = ProjectMember.objects.filter(project=project, user=user).exists()
    is_org_member_and_public = project.is_public and OrganizationMember.objects.filter(organization=project.organization, user=user).exists()

    if not (is_member or is_org_member_and_public or user.is_staff):
        return render(request, 'base/error.html', {'message': 'You do not have permission to view this project.'}, status=403)

    # Get the boards for this project
    boards = Board.objects.filter(project=project)
    
    # Get the default board if it exists, otherwise use the first board
    default_board = boards.filter(is_default=True).first() or boards.first()
    
    return render(request, 'project/detail.html', {
        'project': project,
        'boards': boards,
        'default_board': default_board
    })


# View for rendering the board detail HTML page
def board_detail_view(request, project_id, board_id):
    """
    View function for rendering the board page with board object in context
    """
    project = get_object_or_404(Project, id=project_id)
    board = get_object_or_404(Board, id=board_id, project=project)
    user = request.user
    
    # Permission check: user must be a member of the project or the project must be public
    is_member = ProjectMember.objects.filter(project=project, user=user).exists()
    is_org_member_and_public = project.is_public and OrganizationMember.objects.filter(organization=project.organization, user=user).exists()
    
    if not (is_member or is_org_member_and_public or user.is_staff):
        return render(request, 'base/error.html', {'message': 'You do not have permission to view this board.'}, status=403)
    
    # Add board and related objects to context
    context = {
        'board': board,
        'project': project,
        'organization': project.organization
    }
    
    return render(request, 'board/board.html', context)


# View for handling project deletion
def project_delete_view(request, project_id):
    """
    View function for handling project deletion
    Requires POST method and checks if user has admin permissions
    """
    project = get_object_or_404(Project, id=project_id)
    user = request.user
    
    # Only allow POST requests for deletion
    if request.method != 'POST':
        return render(request, 'base/error.html', {
            'message': 'Invalid request method. Project deletion requires a POST request.'
        }, status=405)
    
    # Check if user has admin permissions for this project
    is_admin = ProjectMember.objects.filter(
        project=project, 
        user=user, 
        role__in=[ProjectMember.ADMIN, ProjectMember.OWNER]
    ).exists()
    
    if not (is_admin or user.is_staff):
        return render(request, 'base/error.html', {
            'message': 'You do not have permission to delete this project.'
        }, status=403)
    
    # Store project name for success message
    project_name = project.name
    
    # Delete the project
    project.delete()
    
    # Redirect to dashboard with success message
    from django.contrib import messages
    messages.success(request, f'Project "{project_name}" has been successfully deleted.')
    
    return redirect('dashboard')


# View for creating a new project
def project_create_view(request, org_id):
    """
    View function for creating a new project within an organization
    """
    from organizations.models import Organization
    
    # Get the organization
    organization = get_object_or_404(Organization, id=org_id)
    
    # Check if user is a member of the organization
    is_org_member = OrganizationMember.objects.filter(
        organization=organization,
        user=request.user
    ).exists() or request.user.is_staff
    
    if not is_org_member:
        return render(request, 'base/error.html', {
            'message': 'You do not have permission to create projects in this organization.'
        }, status=403)
    
    if request.method == 'POST':
        # Process form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_public = request.POST.get('is_public') == 'on'
        
        if name:  # Name is required
            # Create the project
            project = Project.objects.create(
                name=name,
                description=description,
                organization=organization,
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None,
                is_public=is_public
            )
            
            # Add the creator as a project admin
            ProjectMember.objects.create(
                project=project,
                user=request.user,
                role='ADMIN'
            )
            
            # Create a default board for the project
            board = Board.objects.create(
                project=project,
                name='Default Board',
                description='Default project board'
            )
            
            # Create default columns for the board
            columns = [
                {'name': 'To Do', 'order': 1},
                {'name': 'In Progress', 'order': 2},
                {'name': 'Done', 'order': 3}
            ]
            
            for column_data in columns:
                Column.objects.create(
                    board=board,
                    name=column_data['name'],
                    order=column_data['order']
                )
            
            # Redirect to the project detail page
            return redirect('project_detail', project_id=project.id)
    
    # Render the project creation form
    return render(request, 'project/create.html', {'organization': organization})
