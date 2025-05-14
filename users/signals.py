from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import UserPreference

User = get_user_model()

# Try to import ActivityLog model if available
try:
    from activitylogs.models import ActivityLog
    ACTIVITY_LOGS_ENABLED = True
except ImportError:
    ACTIVITY_LOGS_ENABLED = False

@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """
    Create user preferences when a new user is created
    """
    if created:
        UserPreference.objects.get_or_create(user=instance)
        
        # Log user creation if activity logs are enabled
        if ACTIVITY_LOGS_ENABLED:
            ActivityLog.objects.create(
                user=instance,  # The user who performed the action (themselves in this case)
                content_type=ContentType.objects.get_for_model(instance),
                object_id=str(instance.id),
                action=ActivityLog.CREATE,
                details=f"User account for {instance.email} was created"
            )

@receiver(post_save, sender=UserPreference)
def log_preference_update(sender, instance, created, **kwargs):
    """
    Log when user preferences are updated
    """
    if not created and ACTIVITY_LOGS_ENABLED:
        ActivityLog.objects.create(
            user=instance.user,
            content_type=ContentType.objects.get_for_model(instance.user),
            object_id=str(instance.user.id),
            action=ActivityLog.UPDATE,
            details=f"User preferences updated"
        ) 