from django.db import models
from users.models import User
from organizations.models import Organization
from tasks.models import Task
from django.utils import timezone
from django.db.models import Count, Q

class ActivityLog(models.Model):
    """Activity log model for audit trails"""
    # Action types
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    ASSIGN = 'assign'
    UNASSIGN = 'unassign'
    MOVE = 'move'
    COMMENT = 'comment'
    LOGIN = 'login'
    LOGOUT = 'logout'
    
    # Entity types
    USER = 'user'
    ORGANIZATION = 'organization'
    PROJECT = 'project'
    BOARD = 'board'
    COLUMN = 'column'
    TASK = 'task'
    COMMENT = 'comment'
    LABEL = 'label'
    
    ACTION_TYPES = [
        (CREATE, 'Create'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
        (ASSIGN, 'Assign'),
        (UNASSIGN, 'Unassign'),
        (MOVE, 'Move'),
        (COMMENT, 'Comment'),
        (LOGIN, 'Login'),
        (LOGOUT, 'Logout'),
    ]
    
    ENTITY_TYPES = [
        (USER, 'User'),
        (ORGANIZATION, 'Organization'),
        (PROJECT, 'Project'),
        (BOARD, 'Board'),
        (COLUMN, 'Column'),
        (TASK, 'Task'),
        (COMMENT, 'Comment'),
        (LABEL, 'Label'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_user_activities')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    entity_id = models.PositiveIntegerField()
    entity_name = models.CharField(max_length=255, blank=True, null=True)
    details = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user.username} {self.action_type} {self.entity_type} at {self.timestamp}"

class ProjectMetric(models.Model):
    """Project metrics for analytics"""
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    tasks_total = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    tasks_in_progress = models.PositiveIntegerField(default=0)
    tasks_overdue = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['project', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"Metrics for {self.project.name} on {self.date}"
    
    @classmethod
    def update_metrics_for_project(cls, project, date=None):
        """Update or create metrics for a project for a specific date"""
        if date is None:
            date = timezone.now().date()
        
        # Calculate metrics
        tasks_total = Task.objects.filter(column__board__project=project).count()
        
        # Tasks in progress (not in first or last column)
        tasks_in_progress = Task.objects.filter(
            column__board__project=project, 
            column__order__gt=0, 
        ).exclude(
            column=project.boards.first().columns.last()
        ).count()
        
        # Find the last column which is typically "Done" or "Completed"
        completed_column = project.boards.first().columns.last()
        tasks_completed = Task.objects.filter(column=completed_column).count()
        
        # Tasks overdue
        tasks_overdue = Task.objects.filter(
            column__board__project=project,
            due_date__lt=timezone.now().date(),
        ).exclude(
            column=completed_column
        ).count()
        
        # Active users (users with activity in the last 7 days)
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        active_users = ActivityLog.objects.filter(
            project=project,
            timestamp__gte=seven_days_ago
        ).values('user').distinct().count()
        
        # Update or create metrics record
        metric, created = cls.objects.update_or_create(
            project=project,
            date=date,
            defaults={
                'tasks_total': tasks_total,
                'tasks_completed': tasks_completed,
                'tasks_in_progress': tasks_in_progress,
                'tasks_overdue': tasks_overdue,
                'active_users': active_users
            }
        )
        
        return metric

class UserProductivity(models.Model):
    """User productivity metrics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productivity')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='user_productivity')
    date = models.DateField()
    tasks_completed = models.PositiveIntegerField(default=0)
    tasks_created = models.PositiveIntegerField(default=0)
    comments_created = models.PositiveIntegerField(default=0)
    total_activity = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'project', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.user.username}'s productivity on {self.date} for {self.project.name}"
    
    @classmethod
    def update_for_user_and_project(cls, user, project, date=None):
        """Update or create productivity metrics for a user on a project"""
        if date is None:
            date = timezone.now().date()
        
        # Get the completed column
        completed_column = project.boards.first().columns.last()
        
        # Tasks completed today
        tasks_completed = ActivityLog.objects.filter(
            user=user,
            project=project,
            action_type=ActivityLog.MOVE,
            entity_type=ActivityLog.TASK,
            details__contains={'destination_column': completed_column.id},
            timestamp__date=date
        ).count()
        
        # Tasks created today
        tasks_created = ActivityLog.objects.filter(
            user=user,
            project=project,
            action_type=ActivityLog.CREATE,
            entity_type=ActivityLog.TASK,
            timestamp__date=date
        ).count()
        
        # Comments created today
        comments_created = ActivityLog.objects.filter(
            user=user,
            project=project,
            action_type=ActivityLog.COMMENT,
            entity_type=ActivityLog.COMMENT,
            timestamp__date=date
        ).count()
        
        # Total activity count
        total_activity = ActivityLog.objects.filter(
            user=user,
            project=project,
            timestamp__date=date
        ).count()
        
        # Update or create productivity record
        productivity, created = cls.objects.update_or_create(
            user=user,
            project=project,
            date=date,
            defaults={
                'tasks_completed': tasks_completed,
                'tasks_created': tasks_created,
                'comments_created': comments_created,
                'total_activity': total_activity
            }
        )
        
        return productivity
