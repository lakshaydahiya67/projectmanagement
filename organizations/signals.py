from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Organization, OrganizationMember, OrganizationInvitation

# Try to import ActivityLog model if available
try:
    from activitylogs.models import ActivityLog
    ACTIVITY_LOGS_ENABLED = True
except ImportError:
    ACTIVITY_LOGS_ENABLED = False

@receiver(post_save, sender=Organization)
def organization_created_handler(sender, instance, created, **kwargs):
    """Log when a new organization is created"""
    if created and ACTIVITY_LOGS_ENABLED:
        ActivityLog.objects.create(
            user=instance.members.first().user if instance.members.exists() else None,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=str(instance.id),
            action=ActivityLog.CREATE,
            details=f"Organization '{instance.name}' was created"
        )

@receiver(post_save, sender=OrganizationMember)
def organization_member_handler(sender, instance, created, **kwargs):
    """Log when a user is added to an organization"""
    if created and ACTIVITY_LOGS_ENABLED:
        ActivityLog.objects.create(
            user=instance.user,
            content_type=ContentType.objects.get_for_model(instance.organization),
            object_id=str(instance.organization.id),
            action=ActivityLog.UPDATE,
            details=f"{instance.user.get_full_name()} joined organization '{instance.organization.name}' with role {instance.get_role_display()}"
        )

@receiver(post_save, sender=OrganizationInvitation)
def invitation_handler(sender, instance, created, **kwargs):
    """Log when an invitation is created or updated"""
    if ACTIVITY_LOGS_ENABLED:
        if created:
            ActivityLog.objects.create(
                user=instance.invited_by,
                content_type=ContentType.objects.get_for_model(instance.organization),
                object_id=str(instance.organization.id),
                action=ActivityLog.UPDATE,
                details=f"Invitation sent to {instance.email} for organization '{instance.organization.name}'"
            )
        elif instance.accepted and 'accepted' in kwargs.get('update_fields', []):
            ActivityLog.objects.create(
                user=instance.invited_by,  # We don't have the user who accepted here, will be created by OrganizationMember signal
                content_type=ContentType.objects.get_for_model(instance.organization),
                object_id=str(instance.organization.id),
                action=ActivityLog.UPDATE,
                details=f"Invitation to {instance.email} for organization '{instance.organization.name}' was accepted"
            ) 