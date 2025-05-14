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
            'details', 'timestamp'
        ]
        read_only_fields = fields

class ProjectMetricSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectMetric
        fields = [
            'id', 'project', 'project_name', 'date', 'tasks_total',
            'tasks_completed', 'tasks_in_progress', 'tasks_overdue',
            'active_users', 'completion_rate'
        ]
        read_only_fields = fields
    
    def get_completion_rate(self, obj):
        """Calculate the task completion rate as a percentage"""
        if obj.tasks_total == 0:
            return 0
        return round((obj.tasks_completed / obj.tasks_total) * 100, 2)

class UserProductivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = UserProductivity
        fields = [
            'id', 'user', 'user_name', 'project', 'project_name',
            'date', 'tasks_created', 'tasks_completed', 'comments_created',
            'total_activity'
        ]
        read_only_fields = fields
