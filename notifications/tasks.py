from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
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
        assigned_by = User.objects.get(id=assigned_by_id)
        
        # Create notification in database
        notification = Notification.objects.create(
            recipient=user,
            notification_type=Notification.TASK_ASSIGNED,
            title=f"New task assigned: {task.title}",
            message=f"{assigned_by.get_full_name()} assigned you a task: {task.title}",
            content_type=task.__class__._meta.get_contenttypes_for_model()[0],
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
                    content_type=task.__class__._meta.get_contenttypes_for_model()[0],
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
        due_date__lt=timezone.now(),
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
                    content_type=task.__class__._meta.get_contenttypes_for_model()[0],
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
        f"{assigned_by.get_full_name()} has assigned you to the task '{task.title}'.\n\n"
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
        'id': notification.id,
        'type': notification.notification_type,
        'title': notification.title,
        'message': notification.message,
        'created_at': notification.created_at.isoformat(),
        'read': notification.read,
    }
    
    # Send to user's notification group
    async_to_sync(channel_layer.group_send)(
        f'user_notifications_{notification.recipient.id}',
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )
