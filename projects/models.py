from django.db import models
from organizations.models import Organization
from users.models import User
from django.utils import timezone
import uuid

class Project(models.Model):
    """Project model that belongs to an organization"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name

class ProjectMember(models.Model):
    """Association model between Project and User with roles"""
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'
    VIEWER = 'viewer'
    
    ROLE_CHOICES = [
        (OWNER, 'Owner'),
        (ADMIN, 'Admin'),
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
        
class Board(models.Model):
    """Board model that belongs to a project (Kanban board)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='boards')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_boards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.project.name}"
    
class Column(models.Model):
    """Column model for Kanban board"""
    name = models.CharField(max_length=100)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='columns')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wip_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Work in progress limit")
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return f"{self.name} - {self.board.name}"
