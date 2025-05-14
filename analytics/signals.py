from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from projects.models import Project
from tasks.models import Task
from .models import ProjectMetric, UserProductivity
from django.utils import timezone

@receiver(post_save, sender=Task)
def update_project_metrics_on_task_change(sender, instance, **kwargs):
    """
    When a task is saved, update the project metrics
    """
    project = instance.column.board.project
    today = timezone.now().date()
    ProjectMetric.update_metrics_for_project(project, today)
    
    # Update user productivity for any assigned users
    for assignee in instance.assignees.all():
        UserProductivity.update_for_user_and_project(assignee, project, today)

@receiver(post_delete, sender=Task)
def update_project_metrics_on_task_delete(sender, instance, **kwargs):
    """
    When a task is deleted, update the project metrics
    """
    try:
        project = instance.column.board.project
        today = timezone.now().date()
        ProjectMetric.update_metrics_for_project(project, today)
    except:
        # Project might already be deleted
        pass 