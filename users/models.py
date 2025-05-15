from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import os
import uuid

def validate_image_size(image):
    """Validate that the image is not too large (max 5MB)"""
    file_size = image.file.size
    limit_mb = 5
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Max size of file is {limit_mb} MB")

def user_profile_picture_path(instance, filename):
    """Generate a unique path for user profile pictures"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('profile_pictures', filename)

class User(AbstractUser):
    """Custom user model that extends Django's AbstractUser"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path, 
        null=True, 
        blank=True,
        validators=[validate_image_size]
    )
    phone_number = models.CharField(
        max_length=15, 
        null=True, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    job_title = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})" if self.get_full_name() else self.email
    
    def clean(self):
        super().clean()
        # Ensure email is lowercase for consistency
        if self.email:
            self.email = self.email.lower()
    
    def get_profile_picture_url(self):
        """Return the complete URL for the profile picture or None if not available"""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return None

class UserPreference(models.Model):
    """User preferences model to store user-specific settings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    theme_preference = models.CharField(
        max_length=20,
        choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System')],
        default='system'
    )
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s preferences"
