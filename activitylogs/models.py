from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import User
import uuid

class ActivityLog(models.Model):
    """Model for tracking all user actions in the system"""
    
    # Action types
    CREATED = 'created'
    UPDATED = 'updated'
    DELETED = 'deleted'
    COMMENTED = 'commented'
    ASSIGNED = 'assigned'
    MOVED = 'moved'
    
    ACTION_TYPES = [
        (CREATED, 'Created'),
        (UPDATED, 'Updated'),
        (DELETED, 'Deleted'),
        (COMMENTED, 'Commented'),
        (ASSIGNED, 'Assigned'),
        (MOVED, 'Moved'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activitylogs_activities')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Generic foreign key to allow association with any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional metadata about the action
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Project relation for easy filtering by project
    project_id = models.UUIDField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['project_id']),
        ]
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} {self.get_action_type_display()} {self.content_type.model} at {self.timestamp}"
    
    @classmethod
    def log_activity(cls, user, action_type, content_object, description=None, metadata=None, ip_address=None, project_id=None):
        """
        Helper method to create activity log entries
        
        Args:
            user: The user who performed the action
            action_type: Type of action from ACTION_TYPES
            content_object: The object the action was performed on
            description: Text description of the action
            metadata: Additional JSON data about the action
            ip_address: IP address of the user
            project_id: Optional project ID for filtering
        """
        
        content_type = ContentType.objects.get_for_model(content_object)
        
        # Get project_id if not provided but can be derived
        if not project_id:
            # Try common attributes that might link to a project
            if hasattr(content_object, 'project_id'):
                project_id = content_object.project_id
            elif hasattr(content_object, 'project'):
                project_id = content_object.project.id
            elif hasattr(content_object, 'board') and hasattr(content_object.board, 'project'):
                project_id = content_object.board.project.id
            elif hasattr(content_object, 'column') and hasattr(content_object.column, 'board'):
                project_id = content_object.column.board.project.id
        
        # Create the activity log entry
        return cls.objects.create(
            user=user,
            action_type=action_type,
            content_type=content_type,
            object_id=content_object.id,
            description=description,
            metadata=metadata or {},
            ip_address=ip_address,
            project_id=project_id
        ) 