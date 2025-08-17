from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
import json

from .models import Notification, NotificationSetting
import datetime

User = get_user_model()

def send_task_assigned_notification(task_id, user_id, assigned_by_id):
    """
    Send notification synchronously when a task is assigned to a user
    """
    from tasks.models import Task
    
    try:
        task = Task.objects.get(id=task_id)
        user = User.objects.get(id=user_id)
        assigned_by = User.objects.get(id=assigned_by_id) if assigned_by_id else None
        
        # Create notification in database
        notification = Notification.objects.create(
            recipient=user,
            notification_type=Notification.TASK_ASSIGNED,
            title=f"New task assigned: {task.title}",
            message=f"{assigned_by.get_full_name() if assigned_by else 'Someone'} assigned you a task: {task.title}",
            content_type=ContentType.objects.get_for_model(task),
            object_id=task.id
        )
        
        # Check if user wants email notifications for task assignments
        try:
            settings = NotificationSetting.objects.get(user=user)
            if settings.email_task_assigned:
                send_task_assignment_email(user.email, task, assigned_by)
        except NotificationSetting.DoesNotExist:
            # Default to sending email if settings don't exist
            send_task_assignment_email(user.email, task, assigned_by)
        
        # Send real-time notification via WebSocket
        send_realtime_notification(notification)
        
        return notification
    except Exception as e:
        print(f"Error sending task assignment notification: {str(e)}")
        return None

def send_comment_notification(comment_id):
    """
    Send notification synchronously when a comment is added to a task
    """
    from tasks.models import Comment
    
    try:
        comment = Comment.objects.get(id=comment_id)
        task = comment.task
        
        # Get task assignees and other commenters (excluding the comment creator)
        recipients = set()
        
        # Add task assignees
        for assignee in task.assignees.all():
            if assignee != comment.user:
                recipients.add(assignee)
        
        # Add other commenters
        for other_comment in task.comments.all():
            if other_comment.user != comment.user:
                recipients.add(other_comment.user)
        
        notifications = []
        
        # Create a notification for each recipient
        for recipient in recipients:
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=Notification.COMMENT_ADDED,
                title=f"New comment on task: {task.title}",
                message=f"{comment.user.get_full_name()} commented: {comment.text[:50]}{'...' if len(comment.text) > 50 else ''}",
                content_type=ContentType.objects.get_for_model(task),
                object_id=task.id
            )
            notifications.append(notification)
            
            # Check if user wants email notifications for comments
            try:
                settings = NotificationSetting.objects.get(user=recipient)
                if settings.email_comment_added:
                    send_comment_email(recipient.email, task, comment)
            except NotificationSetting.DoesNotExist:
                # Default to sending email if settings don't exist
                send_comment_email(recipient.email, task, comment)
            
            # Send real-time notification via WebSocket
            send_realtime_notification(notification)
            
        return notifications
    except Exception as e:
        print(f"Error sending comment notification: {str(e)}")
        return []

def send_task_assignment_email(email, task, assigned_by):
    """
    Send email notification for task assignment
    """
    subject = f"New Task Assigned: {task.title}"
    message = (
        f"You have been assigned a new task by {assigned_by.get_full_name() if assigned_by else 'Someone'}.\n\n"
        f"Task: {task.title}\n"
        f"Description: {task.description}\n"
        f"Due Date: {task.due_date if task.due_date else 'Not set'}\n\n"
        f"View task details at: {settings.BASE_URL}/projects/{task.column.board.project.id}/tasks/{task.id}/"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=True,
    )

def send_comment_email(email, task, comment):
    """
    Send email notification for new comment
    """
    subject = f"New Comment on Task: {task.title}"
    message = (
        f"{comment.user.get_full_name()} commented on task '{task.title}':\n\n"
        f'"{comment.text}"\n\n'
        f"View task and respond at: {settings.BASE_URL}/projects/{task.column.board.project.id}/tasks/{task.id}/"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=True,
    )

def send_realtime_notification(notification):
    """
    Send a real-time notification via WebSocket
    """
    if not CHANNELS_AVAILABLE:
        return  # Skip WebSocket notifications if channels not available
        
    try:
        channel_layer = get_channel_layer()
        user_channel = f"notifications_{notification.recipient.id}"
        
        async_to_sync(channel_layer.group_send)(
            user_channel,
            {
                "type": "send_notification",
                "message": json.dumps({
                    "id": str(notification.id),
                    "type": notification.notification_type,
                    "title": notification.title,
                    "message": notification.message,
                    "timestamp": notification.created_at.isoformat(),
                    "read": notification.read,
                })
            }
        )
    except Exception as e:
        print(f"Error sending realtime notification: {str(e)}")
