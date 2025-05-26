from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from users.models import User
import uuid
import os

# Optional import for enhanced MIME type validation
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

def validate_attachment_file(file):
    """Secure validation for task attachment files"""
    # Size validation (max 10MB)
    file_size = file.file.size
    limit_mb = 10
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"File size too large. Maximum size is {limit_mb} MB")
    
    # Validate file extension - allow common safe file types
    allowed_extensions = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.txt', '.csv', '.zip', '.rar', '.7z',
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mp3', '.wav'
    ]
    
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    # Dangerous file extensions that should never be allowed
    dangerous_extensions = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.sh', '.ps1', '.php', '.asp', '.aspx', '.jsp'
    ]
    
    if ext in dangerous_extensions:
        raise ValidationError("Executable files are not allowed for security reasons")
    
    # Basic MIME type validation using python-magic if available
    if HAS_MAGIC:
        try:
            file.file.seek(0)
            file_data = file.file.read(1024)  # Read first 1KB
            file.file.seek(0)  # Reset pointer
            
            mime_type = magic.from_buffer(file_data, mime=True)
            
            # Block dangerous MIME types
            dangerous_mime_types = [
                'application/x-executable', 'application/x-msdownload',
                'application/x-msdos-program', 'application/x-bat'
            ]
            
            if mime_type in dangerous_mime_types:
                raise ValidationError("File type not allowed for security reasons")
                
        except Exception:
            # If python-magic not available, rely on extension check
            pass

def secure_attachment_path(instance, filename):
    """Generate secure path for task attachments"""
    # Remove any path traversal attempts
    filename = os.path.basename(filename)
    
    # Generate unique filename to prevent conflicts and information disclosure
    ext = os.path.splitext(filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    return os.path.join('task_attachments', str(instance.task.id), unique_filename)
# Use string references for foreign keys to avoid circular imports
# from projects.models import Project, Column

class Label(models.Model):
    """Label model for tasks"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default="#1E88E5")  # Default blue color
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='labels')
    
    class Meta:
        unique_together = ['name', 'project']
        
    def __str__(self):
        return f"{self.name} ({self.project.name})"

class Task(models.Model):
    """Task model (card in Kanban board)"""
    # Priority choices
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'
    
    PRIORITY_CHOICES = [
        (LOW, 'Low'),
        (MEDIUM, 'Medium'),
        (HIGH, 'High'),
        (URGENT, 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    column = models.ForeignKey('projects.Column', on_delete=models.CASCADE, related_name='tasks')
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=MEDIUM)
    labels = models.ManyToManyField(Label, related_name='tasks', blank=True)
    assignees = models.ManyToManyField(User, related_name='assigned_tasks', blank=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['order']
        constraints = [
            models.CheckConstraint(
                check=models.Q(estimated_hours__gt=0) | models.Q(estimated_hours__isnull=True),
                name='task_estimated_hours_positive'
            ),
            models.CheckConstraint(
                check=models.Q(actual_hours__gt=0) | models.Q(actual_hours__isnull=True),
                name='task_actual_hours_positive'
            )
            # Note: SQLite doesn't support length constraints, so title validation is handled at the form/serializer level
        ]
    
    def __str__(self):
        return self.title
        
    @property
    def is_overdue(self):
        if self.due_date:
            return timezone.now() > self.due_date
        return False
    
class Comment(models.Model):
    """Comment model for tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"

class Attachment(models.Model):
    """Attachment model for tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=secure_attachment_path, validators=[validate_attachment_file])
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_attachments')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(file_size__gt=0),
                name='attachment_file_size_positive'
            )
            # Note: SQLite doesn't support length constraints, so filename validation is handled at the form/serializer level
        ]
    
    def __str__(self):
        return self.filename
