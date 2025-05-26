from rest_framework import serializers
from .models import Project, ProjectMember, Board, Column, BoardViewer
from users.serializers import UserSerializer
from organizations.serializers import OrganizationSerializer
from organizations.models import Organization

class ColumnSerializer(serializers.ModelSerializer):
    # Override fields with custom error messages
    name = serializers.CharField(
        max_length=100,
        error_messages={
            'blank': 'Column name cannot be blank.',
            'required': 'Column name is required.',
            'null': 'Column name cannot be null.',
            'max_length': 'Column name cannot exceed 100 characters.'
        }
    )
    
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all(),  # Default queryset, will be filtered in __init__
        error_messages={
            'required': 'Board is required.',
            'null': 'Board cannot be null.',
            'does_not_exist': 'Selected board does not exist.',
            'incorrect_type': 'Invalid board format.'
        }
    )
    
    order = serializers.IntegerField(
        required=False,
        error_messages={
            'invalid': 'Order must be a valid number.',
            'null': 'Order cannot be null if provided.'
        }
    )
    
    wip_limit = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={
            'invalid': 'WIP limit must be a valid number.',
            'min_value': 'WIP limit must be greater than 0.'
        }
    )
    
    class Meta:
        model = Column
        fields = ['id', 'name', 'board', 'order', 'wip_limit', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set board queryset based on user's accessible boards
        if self.context and 'request' in self.context:
            user = self.context['request'].user
            user_projects = ProjectMember.objects.filter(user=user).values_list('project', flat=True)
            self.fields['board'].queryset = Board.objects.filter(project__in=user_projects)
        else:
            self.fields['board'].queryset = Board.objects.none()

class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)
    
    # Override fields with custom error messages
    name = serializers.CharField(
        max_length=100,
        error_messages={
            'blank': 'Board name cannot be blank.',
            'required': 'Board name is required.',
            'null': 'Board name cannot be null.',
            'max_length': 'Board name cannot exceed 100 characters.'
        }
    )
    
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),  # Default queryset, will be filtered in __init__
        error_messages={
            'required': 'Project is required.',
            'null': 'Project cannot be null.',
            'does_not_exist': 'Selected project does not exist.',
            'incorrect_type': 'Invalid project format.'
        }
    )
    
    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'project', 'created_by', 'created_at', 'updated_at', 'is_default', 'columns']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Check if we're in a nested context (creating board for a specific project)
        view = self.context.get('view')
        if view and hasattr(view, 'kwargs') and 'project_pk' in view.kwargs:
            # In nested context, project comes from URL, so make it not required
            self.fields['project'].required = False
            self.fields['project'].allow_null = True
        
        # Set project queryset based on user's accessible projects
        if self.context and 'request' in self.context:
            user = self.context['request'].user
            user_projects = ProjectMember.objects.filter(user=user).values_list('project', flat=True)
            self.fields['project'].queryset = Project.objects.filter(id__in=user_projects)
        else:
            self.fields['project'].queryset = Project.objects.none()
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)

class BoardViewerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BoardViewer
        fields = ['id', 'user', 'joined_at', 'last_activity']
        read_only_fields = ['joined_at', 'last_activity']

class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'project', 'role', 'role_display', 'joined_at']
        read_only_fields = ['joined_at']

class ProjectMemberCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = ['user', 'project', 'role']

class ProjectSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    # Override fields with custom error messages
    name = serializers.CharField(
        max_length=100,
        error_messages={
            'blank': 'Project name cannot be blank.',
            'required': 'Project name is required.',
            'null': 'Project name cannot be null.',
            'max_length': 'Project name cannot exceed 100 characters.'
        }
    )
    
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),  # Default queryset, will be filtered in __init__
        error_messages={
            'required': 'Organization is required.',
            'null': 'Organization cannot be null.',
            'does_not_exist': 'Selected organization does not exist.',
            'incorrect_type': 'Invalid organization format.'
        }
    )
    
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        error_messages={
            'max_length': 'Description is too long.'
        }
    )
    
    start_date = serializers.DateField(
        required=False,
        error_messages={
            'invalid': 'Start date must be in YYYY-MM-DD format.',
            'null': 'Start date cannot be null if provided.'
        }
    )
    
    end_date = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={
            'invalid': 'End date must be in YYYY-MM-DD format.'
        }
    )
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'organization', 'organization_name',
            'created_by', 'created_at', 'updated_at', 'start_date', 
            'end_date', 'is_active', 'is_public', 'slug'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set organization queryset based on user's accessible organizations
        if self.context and 'request' in self.context:
            user = self.context['request'].user
            from organizations.models import Organization, OrganizationMember
            user_orgs = OrganizationMember.objects.filter(user=user).values_list('organization', flat=True)
            self.fields['organization'].queryset = Organization.objects.filter(id__in=user_orgs)
        else:
            from organizations.models import Organization
            self.fields['organization'].queryset = Organization.objects.all()
    
    def validate(self, data):
        """Custom validation with descriptive error messages"""
        errors = {}
        
        # Validate end_date is after start_date
        if 'start_date' in data and 'end_date' in data and data['end_date']:
            if data['end_date'] < data['start_date']:
                errors['end_date'] = 'End date must be after the start date.'
        
        # Validate organization membership
        if 'organization' in data:
            user = self.context['request'].user
            from organizations.models import OrganizationMember
            if not OrganizationMember.objects.filter(
                user=user, 
                organization=data['organization']
            ).exists():
                errors['organization'] = 'You do not have permission to create projects in this organization.'
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        project = super().create(validated_data)
        
        # Create default board and columns
        board = Board.objects.create(
            name="Default Board",
            description="Default board created automatically",
            project=project,
            created_by=user,
            is_default=True
        )
        
        # Create default columns
        Column.objects.create(name="To Do", board=board, order=0)
        Column.objects.create(name="In Progress", board=board, order=1)
        Column.objects.create(name="Review", board=board, order=2)
        Column.objects.create(name="Done", board=board, order=3)
        
        # Add creator as project owner
        ProjectMember.objects.create(
            project=project,
            user=user,
            role=ProjectMember.OWNER
        )
        
        return project

class ProjectDetailSerializer(ProjectSerializer):
    boards = BoardSerializer(many=True, read_only=True)
    members_count = serializers.SerializerMethodField()
    
    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['boards', 'members_count']
    
    def get_members_count(self, obj):
        return obj.members.count()
