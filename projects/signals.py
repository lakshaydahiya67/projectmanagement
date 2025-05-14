from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Project, ProjectMember, Board, Column

# Try to import ActivityLog model if available
try:
    from activitylogs.models import ActivityLog
    ACTIVITY_LOGS_ENABLED = True
except ImportError:
    ACTIVITY_LOGS_ENABLED = False

@receiver(post_save, sender=Project)
def project_created_handler(sender, instance, created, **kwargs):
    """Log when a new project is created"""
    if created and ACTIVITY_LOGS_ENABLED:
        ActivityLog.objects.create(
            user=instance.created_by,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=str(instance.id),
            action=ActivityLog.CREATE,
            details=f"Project '{instance.name}' was created"
        )

@receiver(post_save, sender=ProjectMember)
def project_member_handler(sender, instance, created, **kwargs):
    """Log when a user is added to a project"""
    if created and ACTIVITY_LOGS_ENABLED:
        ActivityLog.objects.create(
            user=instance.user,
            content_type=ContentType.objects.get_for_model(instance.project),
            object_id=str(instance.project.id),
            action=ActivityLog.UPDATE,
            details=f"{instance.user.get_full_name()} joined project '{instance.project.name}' with role {instance.get_role_display()}"
        )

@receiver(post_save, sender=Board)
def board_created_handler(sender, instance, created, **kwargs):
    """Log when a new board is created"""
    if created and ACTIVITY_LOGS_ENABLED:
        ActivityLog.objects.create(
            user=instance.created_by,
            content_type=ContentType.objects.get_for_model(instance.project),
            object_id=str(instance.project.id),
            action=ActivityLog.UPDATE,
            details=f"Board '{instance.name}' was created for project '{instance.project.name}'"
        )

@receiver(post_save, sender=Column)
def column_created_handler(sender, instance, created, **kwargs):
    """Log when a new column is created"""
    if created and ACTIVITY_LOGS_ENABLED:
        # Try to get the board's creator as the user
        user = instance.board.created_by
        
        ActivityLog.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(instance.board.project),
            object_id=str(instance.board.project.id),
            action=ActivityLog.UPDATE,
            details=f"Column '{instance.name}' was added to board '{instance.board.name}'"
        ) 