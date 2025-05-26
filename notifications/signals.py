from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from tasks.models import Task, Comment
from projects.models import ProjectMember
from .utils import (
    send_task_assigned_notification,
    send_comment_notification
)

@receiver(post_save, sender=Comment)
def comment_created_notification(sender, instance, created, **kwargs):
    """Trigger notification when a new comment is created"""
    if created:
        # Send notification synchronously
        send_comment_notification(instance.id)

@receiver(m2m_changed, sender=Task.assignees.through)
def task_assignee_changed(sender, instance, action, pk_set, **kwargs):
    """Trigger notification when a user is assigned to a task"""
    if action == 'post_add' and pk_set:
        # Get the task and the users that were added
        task = instance
        
        # Check who initiated the change
        # Default to the task creator if we can't determine
        assigned_by = getattr(task, '_current_user', task.created_by)
        
        for user_id in pk_set:
            # Don't notify users who assign themselves
            if assigned_by and user_id == assigned_by.id:
                continue
                
            # Send notification synchronously
            send_task_assigned_notification(
                task_id=task.id,
                user_id=user_id,
                assigned_by_id=assigned_by.id if assigned_by else None
            )

@receiver(post_save, sender=ProjectMember)
def project_member_added(sender, instance, created, **kwargs):
    """Trigger notification when a user is added to a project"""
    if created:
        from .models import Notification
        from .utils import send_realtime_notification
        
        # Create notification for the added user
        notification = Notification.objects.create(
            recipient=instance.user,
            notification_type=Notification.PROJECT_ADDED,
            title=f"Added to project: {instance.project.name}",
            message=f"You have been added to the project '{instance.project.name}'",
            content_type=ContentType.objects.get_for_model(instance.project),
            object_id=instance.project.id
        )
        
        # Send real-time notification
        send_realtime_notification(notification) 