from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from projects.models import Project, Board, Column, ProjectMember
from tasks.models import Task, Comment, Attachment, Label
from organizations.models import Organization, OrganizationMember
from .models import ActivityLog

# Helper function to determine if signal was triggered by model creation
def is_create(instance, created=None, **kwargs):
    if created is not None:  # from post_save signal
        return created
    # For post_delete and other signals
    return False

@receiver(post_save, sender=Project)
def log_project_activity(sender, instance, created, **kwargs):
    if created:
        action_type = ActivityLog.CREATED
    else:
        action_type = ActivityLog.UPDATED
    
    ActivityLog.log_activity(
        user=instance.created_by,
        action_type=action_type,
        content_object=instance,
        description=f"{action_type.capitalize()} project '{instance.name}'",
        project_id=instance.id
    )

@receiver(post_delete, sender=Project)
def log_project_delete(sender, instance, **kwargs):
    if not hasattr(instance, 'created_by') or not instance.created_by:
        return  # Skip if we don't have a user
        
    ActivityLog.log_activity(
        user=instance.created_by,
        action_type=ActivityLog.DELETED,
        content_object=instance,
        description=f"Deleted project '{instance.name}'",
        project_id=instance.id
    )

@receiver(post_save, sender=Board)
def log_board_activity(sender, instance, created, **kwargs):
    if created:
        action_type = ActivityLog.CREATED
    else:
        action_type = ActivityLog.UPDATED
    
    ActivityLog.log_activity(
        user=instance.created_by,
        action_type=action_type,
        content_object=instance,
        description=f"{action_type.capitalize()} board '{instance.name}' in project '{instance.project.name}'",
        project_id=instance.project.id
    )

@receiver(post_save, sender=Task)
def log_task_activity(sender, instance, created, **kwargs):
    if created:
        action_type = ActivityLog.CREATED
    else:
        action_type = ActivityLog.UPDATED
    
    ActivityLog.log_activity(
        user=instance.created_by,
        action_type=action_type,
        content_object=instance,
        description=f"{action_type.capitalize()} task '{instance.title}'",
        project_id=instance.column.board.project.id
    )

@receiver(post_save, sender=Comment)
def log_comment_activity(sender, instance, created, **kwargs):
    if created:
        action_type = ActivityLog.COMMENTED
    else:
        action_type = ActivityLog.UPDATED
    
    task = instance.task
    board = task.column.board
    
    ActivityLog.log_activity(
        user=instance.author,
        action_type=action_type,
        content_object=instance,
        description=f"{action_type.capitalize()} on task '{task.title}'",
        project_id=board.project.id
    )

# Connect the signals to the app's ready method in apps.py 