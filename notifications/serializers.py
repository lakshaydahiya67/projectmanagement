from rest_framework import serializers
from .models import Notification, NotificationSetting

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'notification_type', 'title', 'message', 
                  'created_at', 'read', 'read_at', 'content_type', 'object_id']
        read_only_fields = ['recipient', 'notification_type', 'title', 'message', 
                           'created_at', 'content_type', 'object_id']

class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = [
            'user', 'task_assigned', 'task_updated', 'deadline_approaching',
            'deadline_missed', 'comment_added', 'mentioned', 'project_added',
            'invitation', 'email_task_assigned', 'email_task_updated',
            'email_deadline_approaching', 'email_deadline_missed',
            'email_comment_added', 'email_mentioned', 'email_project_added',
            'email_invitation'
        ]
        read_only_fields = ['user']
