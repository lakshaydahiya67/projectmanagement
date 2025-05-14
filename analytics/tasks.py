from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .models import ProjectMetric, UserProductivity
from tasks.models import Task
from projects.models import Project

@shared_task
def update_project_metrics():
    """
    Update project metrics for all active projects
    """
    today = timezone.now().date()
    projects = Project.objects.filter(is_active=True)
    
    for project in projects:
        ProjectMetric.update_metrics_for_project(project, today)
    
    return f"Updated metrics for {projects.count()} projects"

@shared_task
def generate_user_productivity_metrics():
    """
    Generate productivity metrics for all active users in projects
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get all projects
    projects = Project.objects.filter(is_active=True)
    
    for project in projects:
        # Get all members in the project
        project_members = project.members.all()
        
        for member in project_members:
            user = member.user
            
            # Count tasks created yesterday
            tasks_created = Task.objects.filter(
                column__board__project=project,
                created_by=user,
                created_at__date=yesterday
            ).count()
            
            # Count tasks completed yesterday (moved to "Done" column)
            try:
                done_column = project.boards.first().columns.filter(name__iexact='Done').first()
                if done_column:
                    tasks_completed = Task.objects.filter(
                        column=done_column,
                        assignees=user,
                        updated_at__date=yesterday
                    ).count()
                else:
                    tasks_completed = 0
            except:
                tasks_completed = 0
                
            # Count comments added
            comments_created = user.comments.filter(
                task__column__board__project=project,
                created_at__date=yesterday
            ).count()
            
            # Calculate total activity
            total_activity = tasks_created + tasks_completed + comments_created
            
            # Create or update productivity record
            UserProductivity.objects.update_or_create(
                user=user,
                project=project,
                date=yesterday,
                defaults={
                    'tasks_created': tasks_created,
                    'tasks_completed': tasks_completed,
                    'comments_created': comments_created,
                    'total_activity': total_activity
                }
            )
    
    return "User productivity metrics updated successfully"

@shared_task
def generate_burndown_chart_data(project_id, start_date=None, end_date=None):
    """
    Generate burndown chart data for a specific project
    """
    try:
        project = Project.objects.get(id=project_id)
        
        if not start_date:
            start_date = project.start_date
        if not end_date:
            end_date = project.end_date or (timezone.now().date() + timedelta(days=30))
            
        # Get all tasks in the project
        total_tasks = Task.objects.filter(column__board__project=project).count()
        
        # Calculate ideal burn rate (tasks per day)
        total_days = (end_date - start_date).days
        if total_days <= 0:
            total_days = 1  # Avoid division by zero
        
        ideal_burn_rate = total_tasks / total_days
        
        # Generate daily data points
        burndown_data = []
        remaining_tasks = total_tasks
        
        current_date = start_date
        while current_date <= end_date:
            # Get tasks completed on this day
            completed_tasks = Task.objects.filter(
                column__board__project=project,
                column__name__iexact='Done',
                updated_at__date=current_date
            ).count()
            
            remaining_tasks -= completed_tasks
            
            # Calculate ideal remaining for this day
            days_elapsed = (current_date - start_date).days
            ideal_remaining = max(0, total_tasks - (ideal_burn_rate * days_elapsed))
            
            burndown_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'actual_remaining': remaining_tasks,
                'ideal_remaining': ideal_remaining
            })
            
            # Move to next day
            current_date += timedelta(days=1)
            
        return {
            'project_id': project_id,
            'project_name': project.name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_tasks': total_tasks,
            'burndown_data': burndown_data
        }
            
    except Project.DoesNotExist:
        return f"Project with ID {project_id} not found"
    except Exception as e:
        return f"Error generating burndown chart data: {str(e)}"
