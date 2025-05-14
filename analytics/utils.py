from django.utils import timezone
from datetime import timedelta
from .models import ProjectMetric, UserProductivity, ActivityLog
from tasks.models import Task
from projects.models import Project
import logging

logger = logging.getLogger(__name__)

def validate_project_metrics():
    """
    Validate all project metrics and recalculate any that are inconsistent
    """
    try:
        # Get all project metrics from the last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        metrics = ProjectMetric.objects.filter(date__gte=thirty_days_ago)
        
        fixed_count = 0
        for metric in metrics:
            project = metric.project
            
            # Calculate the expected values
            tasks_total = Task.objects.filter(column__board__project=project).count()
            
            # Check if metrics match actual data
            if metric.tasks_total != tasks_total:
                # Recalculate metrics
                ProjectMetric.update_metrics_for_project(project, metric.date)
                fixed_count += 1
                
        return f"Validated {metrics.count()} project metrics, fixed {fixed_count} inconsistencies"
    
    except Exception as e:
        logger.error(f"Error validating project metrics: {str(e)}")
        return f"Error validating project metrics: {str(e)}"
        
def recalculate_all_metrics(days=7):
    """
    Recalculate all metrics for the specified number of days
    """
    try:
        today = timezone.now().date()
        start_date = today - timedelta(days=days)
        
        # Get all active projects
        projects = Project.objects.filter(is_active=True)
        
        project_metrics_count = 0
        user_productivity_count = 0
        
        # Recalculate metrics for each day and project
        current_date = start_date
        while current_date <= today:
            for project in projects:
                # Update project metrics
                ProjectMetric.update_metrics_for_project(project, current_date)
                project_metrics_count += 1
                
                # Update user productivity for all project members
                for member in project.members.all():
                    UserProductivity.update_for_user_and_project(member.user, project, current_date)
                    user_productivity_count += 1
                    
            current_date += timedelta(days=1)
        
        return f"Recalculated {project_metrics_count} project metrics and {user_productivity_count} user productivity records"
        
    except Exception as e:
        logger.error(f"Error recalculating metrics: {str(e)}")
        return f"Error recalculating metrics: {str(e)}" 