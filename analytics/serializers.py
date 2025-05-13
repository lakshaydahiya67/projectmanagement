from rest_framework import serializers
from .models import ActivityLog, ProjectMetric, UserProductivity

class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_name', 'organization', 'project',
            'action_type', 'action_type_display', 'entity_type',
            'entity_type_display', 'entity_id', 'entity_name',
            'description', 'metadata', 'created_at', 'ip_address'
        ]
        read_only_fields = fields

class ProjectMetricSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectMetric
        fields = [
            'id', 'project', 'project_name', 'date', 'tasks_created',
            'tasks_completed', 'tasks_overdue', 'total_tasks',
            'active_users', 'completion_rate'
        ]
        read_only_fields = fields
    
    def get_completion_rate(self, obj):
        """Calculate the task completion rate as a percentage"""
        if obj.total_tasks == 0:
            return 0
        return round((obj.tasks_completed / obj.total_tasks) * 100, 2)

class UserProductivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = UserProductivity
        fields = [
            'id', 'user', 'user_name', 'project', 'project_name',
            'date', 'tasks_created', 'tasks_completed', 'tasks_assigned',
            'comments_added', 'time_tracked'
        ]
        read_only_fields = fields
