from django.db import models
from django.utils import timezone
from users.models import User
from projects.models import Project, Column

class Label(models.Model):
    """Label model for tasks"""
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default="#1E88E5")  # Default blue color
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='labels')
    
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
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name='tasks')
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
    file = models.FileField(upload_to='task_attachments/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_attachments')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    
    def __str__(self):
        return self.filename
