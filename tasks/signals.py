from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Task, Comment, Attachment, Label

# Try to import ActivityLog model if available
try:
    from activitylogs.models import ActivityLog
    ACTIVITY_LOGS_ENABLED = True
except ImportError:
    ACTIVITY_LOGS_ENABLED = False

# Try to import notification utilities if available
try:
    from notifications.utils import send_task_assigned_notification, send_comment_notification
    NOTIFICATIONS_ENABLED = True
except ImportError:
    NOTIFICATIONS_ENABLED = False

@receiver(post_save, sender=Task)
def task_created_handler(sender, instance, created, **kwargs):
    """Log when a new task is created"""
    if created and ACTIVITY_LOGS_ENABLED:
        ActivityLog.objects.create(
            user=instance.created_by,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=str(instance.id),
            action_type=ActivityLog.CREATED,
            description=f"Task '{instance.title}' was created in column '{instance.column.name}'"
        )

@receiver(m2m_changed, sender=Task.assignees.through)
def task_assignees_changed(sender, instance, action, pk_set, **kwargs):
    """Log when task assignees change and send notifications"""
    if action == 'post_add' and pk_set and ACTIVITY_LOGS_ENABLED:
        from users.models import User
        
        # Get the current user who made the change
        assigned_by = getattr(instance, '_current_user', instance.created_by)
        
        # Log this activity
        assignee_names = []
        for user_id in pk_set:
            try:
                user = User.objects.get(id=user_id)
                assignee_names.append(user.get_full_name())
                
                # Send notification to each assignee (synchronously)
                if NOTIFICATIONS_ENABLED and assigned_by and user_id != assigned_by.id:
                    send_task_assigned_notification(
                        task_id=str(instance.id),
                        user_id=user_id,
                        assigned_by_id=assigned_by.id
                    )
            except User.DoesNotExist:
                pass
                
        if assignee_names:
            ActivityLog.objects.create(
                user=assigned_by,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=str(instance.id),
                action_type=ActivityLog.UPDATED,
                description=f"Task '{instance.title}' assigned to {', '.join(assignee_names)}"
            )

@receiver(post_save, sender=Comment)
def comment_created_handler(sender, instance, created, **kwargs):
    """Log when a new comment is added and send notifications"""
    if created:
        if ACTIVITY_LOGS_ENABLED:
            # Create activity log
            ActivityLog.objects.create(
                user=instance.author,
                content_type=ContentType.objects.get_for_model(instance.task),
                object_id=str(instance.task.id),
                action_type=ActivityLog.UPDATED,
                description=f"Comment added to task '{instance.task.title}'"
            )
        
        # Send notification about the new comment
        if NOTIFICATIONS_ENABLED:
            send_comment_notification(instance.id)

@receiver(post_save, sender=Attachment)
def attachment_created_handler(sender, instance, created, **kwargs):
    """Log when a new attachment is uploaded"""
    if created and ACTIVITY_LOGS_ENABLED:
        ActivityLog.objects.create(
            user=instance.uploaded_by,
            content_type=ContentType.objects.get_for_model(instance.task),
            object_id=str(instance.task.id),
            action_type=ActivityLog.UPDATED,
            description=f"File '{instance.filename}' attached to task '{instance.task.title}'"
        ) 