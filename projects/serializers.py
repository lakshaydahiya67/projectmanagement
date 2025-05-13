from rest_framework import serializers
from .models import Project, ProjectMember, Board, Column
from users.serializers import UserSerializer
from organizations.serializers import OrganizationSerializer

class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ['id', 'name', 'board', 'order', 'wip_limit', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)
    
    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'project', 'created_by', 'created_at', 'updated_at', 'is_default', 'columns']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)

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
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'organization', 'organization_name',
            'created_by', 'created_at', 'updated_at', 'start_date', 
            'end_date', 'is_active', 'is_public', 'slug'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
        
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
