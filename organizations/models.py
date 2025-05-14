from django.db import models
from django.utils import timezone
from users.models import User
import uuid
import secrets

class Organization(models.Model):
    """Organization model for multi-tenancy support"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='organization_logos/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class OrganizationMember(models.Model):
    """Association model between User and Organization with roles"""
    ADMIN = 'admin'
    MANAGER = 'manager'
    MEMBER = 'member'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (MEMBER, 'Member'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['user', 'organization']
        
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN
        
    @property
    def is_manager(self):
        return self.role == self.MANAGER or self.role == self.ADMIN
        
class OrganizationInvitation(models.Model):
    """Invitation model for inviting users to an organization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(
        max_length=20, 
        choices=OrganizationMember.ROLE_CHOICES, 
        default=OrganizationMember.MEMBER
    )
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Invitation for {self.email} to {self.organization.name}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
        
    def save(self, *args, **kwargs):
        if not self.token:
            # Generate a secure token
            self.token = secrets.token_urlsafe(32)
            
        if not self.expires_at:
            # Set expiration to 7 days from now
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
            
        super().save(*args, **kwargs)
