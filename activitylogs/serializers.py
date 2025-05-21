from rest_framework import serializers
from .models import ActivityLog
from users.serializers import UserSerializer

class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs"""
    user = UserSerializer(read_only=True)
    content_type_display = serializers.SerializerMethodField()
    action_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'action_type', 'action_type_display', 'timestamp', 
            'content_type', 'content_type_display', 'object_id', 'description', 
            'metadata', 'project_id'
        ]
        read_only_fields = fields
        ref_name = 'ActivityLogAudit'  # Unique reference name for Swagger
    
    def get_content_type_display(self, obj):
        """Get the display name for the content type"""
        return obj.content_type.model.replace('_', ' ').title()
    
    def get_action_type_display(self, obj):
        """Get the display name for the action type"""
        return obj.get_action_type_display() 