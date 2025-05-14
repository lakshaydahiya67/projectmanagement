from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.contenttypes.models import ContentType
import json

from .models import Notification, NotificationSetting
from tasks.models import Task
from projects.models import Project
import datetime

User = get_user_model()

@shared_task
def send_task_assigned_notification(task_id, user_id, assigned_by_id):
    """
    Send notification when a task is assigned to a user
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
        
        return f"Notification for task {task_id} sent to {user.email}"
    except Exception as e:
        return f"Error sending notification: {str(e)}"

@shared_task
def send_comment_notification(comment_id):
    """
    Send notification when a comment is added to a task
    """
    from tasks.models import Comment
    
    try:
        comment = Comment.objects.get(id=comment_id)
        task = comment.task
        commenter = comment.author
        
        # Get all users involved with the task (assignees + creator)
        # but exclude the comment author
        recipients = list(task.assignees.exclude(id=commenter.id))
        
        if task.created_by and task.created_by.id != commenter.id:
            recipients.append(task.created_by)
            
        # Add participants in the comment thread if this is a reply
        if comment.parent:
            thread_participants = Comment.objects.filter(
                parent=comment.parent
            ).values_list('author', flat=True).distinct()
            
            for participant_id in thread_participants:
                if participant_id != commenter.id:
                    try:
                        participant = User.objects.get(id=participant_id)
                        if participant not in recipients:
                            recipients.append(participant)
                    except User.DoesNotExist:
                        pass
        
        # Send notification to each recipient
        for recipient in recipients:
            # Create notification in database
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=Notification.COMMENT_ADDED,
                title=f"New comment on: {task.title}",
                message=f"{commenter.get_full_name()} commented on task: {task.title}",
                content_type=ContentType.objects.get_for_model(task),
                object_id=task.id
            )
            
            # Check if user wants email notifications for comments
            try:
                settings = NotificationSetting.objects.get(user=recipient)
                if settings.email_comment_added:
                    send_comment_email(recipient.email, task, comment, commenter)
            except NotificationSetting.DoesNotExist:
                # Default to sending email if settings don't exist
                send_comment_email(recipient.email, task, comment, commenter)
            
            # Send real-time notification via WebSocket
            send_realtime_notification(notification)
        
        return f"Comment notifications sent for comment {comment_id} on task {task.id}"
    except Exception as e:
        return f"Error sending comment notification: {str(e)}"

@shared_task
def check_approaching_deadlines():
    """
    Check for tasks with approaching deadlines and send notifications
    """
    # Get tasks with deadlines within the next 24 hours
    tomorrow = timezone.now() + datetime.timedelta(hours=24)
    
    tasks = Task.objects.filter(
        due_date__gt=timezone.now(),
        due_date__lte=tomorrow
    )
    
    for task in tasks:
        # Notify all assignees
        for user in task.assignees.all():
            # Check if notification was already sent for this deadline
            if not Notification.objects.filter(
                recipient=user,
                notification_type=Notification.DEADLINE_APPROACHING,
                object_id=task.id,
                created_at__gte=timezone.now() - datetime.timedelta(hours=24)
            ).exists():
                # Create notification
                notification = Notification.objects.create(
                    recipient=user,
                    notification_type=Notification.DEADLINE_APPROACHING,
                    title=f"Approaching deadline: {task.title}",
                    message=f"Task '{task.title}' is due in less than 24 hours",
                    content_type=ContentType.objects.get_for_model(task),
                    object_id=task.id
                )
                
                # Check if user wants email notifications for approaching deadlines
                try:
                    settings = NotificationSetting.objects.get(user=user)
                    if settings.email_deadline_approaching:
                        send_deadline_email(user.email, task, is_missed=False)
                except NotificationSetting.DoesNotExist:
                    # Default to sending email if settings don't exist
                    send_deadline_email(user.email, task, is_missed=False)
                
                # Send real-time notification
                send_realtime_notification(notification)
    
    return f"Checked {tasks.count()} tasks for approaching deadlines"

@shared_task
def check_missed_deadlines():
    """
    Check for tasks with missed deadlines and send notifications
    """
    # Get tasks with deadlines in the past
    tasks = Task.objects.filter(
        due_date__lt=timezone.now()
    ).exclude(
        # Exclude tasks in the "Done" column
        column__name__iexact='Done'
    )
    
    for task in tasks:
        # Notify all assignees
        for user in task.assignees.all():
            # Check if notification was already sent for this missed deadline
            if not Notification.objects.filter(
                recipient=user,
                notification_type=Notification.DEADLINE_MISSED,
                object_id=task.id,
                created_at__gte=timezone.now() - datetime.timedelta(hours=24)
            ).exists():
                # Create notification
                notification = Notification.objects.create(
                    recipient=user,
                    notification_type=Notification.DEADLINE_MISSED,
                    title=f"Missed deadline: {task.title}",
                    message=f"The deadline for task '{task.title}' has passed",
                    content_type=ContentType.objects.get_for_model(task),
                    object_id=task.id
                )
                
                # Check if user wants email notifications for missed deadlines
                try:
                    settings = NotificationSetting.objects.get(user=user)
                    if settings.email_deadline_missed:
                        send_deadline_email(user.email, task, is_missed=True)
                except NotificationSetting.DoesNotExist:
                    # Default to sending email if settings don't exist
                    send_deadline_email(user.email, task, is_missed=True)
                
                # Send real-time notification
                send_realtime_notification(notification)
    
    return f"Checked {tasks.count()} tasks for missed deadlines"

@shared_task
def update_project_metrics():
    """
    Update project metrics for all active projects
    """
    from analytics.models import ProjectMetric
    
    today = timezone.now().date()
    projects = Project.objects.filter(is_active=True)
    
    for project in projects:
        ProjectMetric.update_metrics_for_project(project, today)
    
    return f"Updated metrics for {projects.count()} projects"

# Helper functions

def send_task_assignment_email(email, task, assigned_by):
    """Send an email notification for task assignment"""
    subject = f"New Task Assigned: {task.title}"
    message = (
        f"Hello,\n\n"
        f"{assigned_by.get_full_name() if assigned_by else 'Someone'} has assigned you to the task '{task.title}'.\n\n"
        f"Description: {task.description}\n"
        f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'No due date'}\n"
        f"Priority: {task.get_priority_display()}\n\n"
        f"Click here to view the task: [Task URL]\n\n"
        f"Thank you,\nProject Management Team"
    )
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

def send_comment_email(email, task, comment, commenter):
    """Send an email notification for task comments"""
    subject = f"New Comment on Task: {task.title}"
    message = (
        f"Hello,\n\n"
        f"{commenter.get_full_name()} commented on task '{task.title}':\n\n"
        f"\"{comment.content}\"\n\n"
        f"Click here to view the comment and reply: [Task URL]\n\n"
        f"Thank you,\nProject Management Team"
    )
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

def send_deadline_email(email, task, is_missed=False):
    """Send an email notification for approaching or missed deadlines"""
    if is_missed:
        subject = f"Deadline Missed: {task.title}"
        message = (
            f"Hello,\n\n"
            f"The deadline for task '{task.title}' has passed.\n\n"
            f"Description: {task.description}\n"
            f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Priority: {task.get_priority_display()}\n\n"
            f"Click here to view the task: [Task URL]\n\n"
            f"Thank you,\nProject Management Team"
        )
    else:
        subject = f"Approaching Deadline: {task.title}"
        message = (
            f"Hello,\n\n"
            f"The deadline for task '{task.title}' is approaching (within 24 hours).\n\n"
            f"Description: {task.description}\n"
            f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Priority: {task.get_priority_display()}\n\n"
            f"Click here to view the task: [Task URL]\n\n"
            f"Thank you,\nProject Management Team"
        )
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

def send_realtime_notification(notification):
    """Send a real-time notification via WebSocket"""
    channel_layer = get_channel_layer()
    
    # Serialize notification data
    notification_data = {
        'id': str(notification.id),
        'notification_type': notification.notification_type,
        'title': notification.title,
        'message': notification.message,
        'created_at': notification.created_at.isoformat(),
        'read': notification.read,
    }
    
    # Send to user's notification group
    try:
        async_to_sync(channel_layer.group_send)(
            f'user_notifications_{notification.recipient.id}',
            {
                'type': 'notification_message',
                'notification': notification_data
            }
        )
    except Exception as e:
        # Log the error but don't raise it to prevent breaking task execution
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send WebSocket notification: {str(e)}")
