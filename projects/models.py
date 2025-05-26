from django.db import models
from organizations.models import Organization
from users.models import User
from django.utils import timezone
from django.utils.text import slugify
import uuid
import datetime

def get_today():
    """
    Return today's date (without time component)
    Using a function to avoid serialization issues with model defaults
    """
    return timezone.now().date()

class Project(models.Model):
    """Project model that belongs to an organization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(default=get_today)  # Using a custom function for the default date
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True)
    
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate a unique slug
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Make sure the slug is unique
            while Project.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                
            self.slug = slug
            
        super().save(*args, **kwargs)

class ProjectMember(models.Model):
    """Association model between Project and User with roles"""
    OWNER = 'owner'
    ADMIN = 'admin'
    MANAGER = 'manager'
    MEMBER = 'member'
    VIEWER = 'viewer'
    
    ROLE_CHOICES = [
        (OWNER, 'Owner'),
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (MEMBER, 'Member'),
        (VIEWER, 'Viewer'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['project', 'user']
        
    def __str__(self):
        return f"{self.user.email} - {self.project.name} ({self.get_role_display()})"
    
    @property
    def is_owner(self):
        return self.role == self.OWNER
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.role == self.OWNER
        
    @property
    def is_manager(self):
        return self.role == self.MANAGER or self.is_admin
        
class Board(models.Model):
    """Board model that belongs to a project (Kanban board)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='boards')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_boards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project'],
                condition=models.Q(is_default=True),
                name='one_default_board_per_project'
            )
        ]
    
    def __str__(self):
        return f"{self.name} - {self.project.name}"
    
class Column(models.Model):
    """Column model for Kanban board"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='columns')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wip_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Work in progress limit")
    
    class Meta:
        ordering = ['order']
        constraints = [
            models.CheckConstraint(
                check=models.Q(wip_limit__gt=0) | models.Q(wip_limit__isnull=True),
                name='positive_wip_limit'
            ),
            models.UniqueConstraint(
                fields=['board', 'name'],
                name='unique_column_name_per_board'
            )
        ]
        
    def __str__(self):
        return f"{self.name} - {self.board.name}"
        
    @property
    def task_count(self):
        return self.tasks.count()
        
    @property
    def is_at_wip_limit(self):
        if self.wip_limit is None:
            return False
        return self.task_count >= self.wip_limit


class BoardViewer(models.Model):
    """
    Model to track which users are currently viewing a board
    """
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='viewers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewing_boards')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['board', 'user']
        
    def __str__(self):
        return f"{self.user.username} viewing {self.board.name}"
        
    @classmethod
    def get_active_viewers(cls, board_id):
        """
        Get users who have been active on the board within the last 5 minutes
        """
        five_minutes_ago = timezone.now() - datetime.timedelta(minutes=5)
        return cls.objects.filter(
            board_id=board_id,
            last_activity__gte=five_minutes_ago
        ).select_related('user')
        
    @classmethod
    def add_or_update_viewer(cls, board_id, user_id):
        """
        Add a new viewer or update their last activity timestamp
        """
        obj, created = cls.objects.update_or_create(
            board_id=board_id,
            user_id=user_id,
            defaults={'last_activity': timezone.now()}
        )
        return obj
        
    @classmethod
    def remove_viewer(cls, board_id, user_id):
        """
        Remove a viewer when they disconnect
        """
        cls.objects.filter(board_id=board_id, user_id=user_id).delete()
