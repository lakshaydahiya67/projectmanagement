from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User

class Notification(models.Model):
    """Notification model for user notifications"""
    # Notification types
    TASK_ASSIGNED = 'task_assigned'
    TASK_UPDATED = 'task_updated'
    DEADLINE_APPROACHING = 'deadline_approaching'
    DEADLINE_MISSED = 'deadline_missed'
    COMMENT_ADDED = 'comment_added'
    MENTIONED = 'mentioned'
    PROJECT_ADDED = 'project_added'
    INVITATION = 'invitation'
    
    NOTIFICATION_TYPES = [
        (TASK_ASSIGNED, 'Task Assigned'),
        (TASK_UPDATED, 'Task Updated'),
        (DEADLINE_APPROACHING, 'Deadline Approaching'),
        (DEADLINE_MISSED, 'Deadline Missed'),
        (COMMENT_ADDED, 'Comment Added'),
        (MENTIONED, 'Mentioned'),
        (PROJECT_ADDED, 'Project Added'),
        (INVITATION, 'Invitation'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # For linking notification to any model (task, project, comment, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.TextField(null=True, blank=True)  # Changed to TextField to support UUIDs and other non-integer IDs
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.email}"

class NotificationSetting(models.Model):
    """Settings for user notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    task_assigned = models.BooleanField(default=True)
    task_updated = models.BooleanField(default=True)
    deadline_approaching = models.BooleanField(default=True)
    deadline_missed = models.BooleanField(default=True)
    comment_added = models.BooleanField(default=True)
    mentioned = models.BooleanField(default=True)
    project_added = models.BooleanField(default=True)
    invitation = models.BooleanField(default=True)
    
    # Email notification settings
    email_task_assigned = models.BooleanField(default=True)
    email_task_updated = models.BooleanField(default=False)
    email_deadline_approaching = models.BooleanField(default=True)
    email_deadline_missed = models.BooleanField(default=True)
    email_comment_added = models.BooleanField(default=False)
    email_mentioned = models.BooleanField(default=True)
    email_project_added = models.BooleanField(default=True)
    email_invitation = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Notification settings for {self.user.email}"
