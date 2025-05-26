from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import os
import uuid

# Optional import for enhanced MIME type validation
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

def validate_image_file(image):
    """Comprehensive image validation with security checks"""
    # Size validation (max 2MB for better security)
    file_size = image.file.size
    limit_mb = 2
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"File size too large. Maximum size is {limit_mb} MB")
    
    # Validate file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}")
    
    # MIME type validation using python-magic if available
    if HAS_MAGIC:
        try:
            # Reset file pointer to beginning
            image.file.seek(0)
            file_data = image.file.read(1024)  # Read first 1KB for MIME detection
            image.file.seek(0)  # Reset pointer
            
            mime_type = magic.from_buffer(file_data, mime=True)
            allowed_mime_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp'
            ]
            
            if mime_type not in allowed_mime_types:
                raise ValidationError(f"Invalid file content. Expected image file but got {mime_type}")
                
        except Exception:
            # If magic fails, continue with basic validation
            pass
    
    # Basic dimension check (max 4096x4096 to prevent memory exhaustion)
    try:
        from PIL import Image
        image.file.seek(0)
        with Image.open(image.file) as img:
            width, height = img.size
            max_dimension = 4096
            if width > max_dimension or height > max_dimension:
                raise ValidationError(f"Image dimensions too large. Maximum: {max_dimension}x{max_dimension}")
        image.file.seek(0)  # Reset file pointer
    except ImportError:
        # PIL not available, skip dimension check
        pass

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
        validators=[validate_image_file]
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
    
    # Fix for related_name clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_preferences')
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
