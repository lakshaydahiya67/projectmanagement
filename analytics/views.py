from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, views, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg
from datetime import timedelta
try:
    from django_filters.rest_framework import DjangoFilterBackend
except ImportError:
    DjangoFilterBackend = None  # Make it optional
from rest_framework import filters

from .models import ActivityLog, ProjectMetric, UserProductivity
from .serializers import ActivityLogSerializer, ProjectMetricSerializer, UserProductivitySerializer
from projects.models import Project, Board
from projects.serializers import BoardSerializer
from tasks.models import Task
from tasks.serializers import TaskSerializer
from users.models import User

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for activity logs
    """
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Only add filter backends if they're available
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    if DjangoFilterBackend:
        filter_backends.append(DjangoFilterBackend)
        
    filterset_fields = ['action_type', 'entity_type', 'user', 'project']
    search_fields = ['entity_name']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        if 'organization_pk' in self.kwargs:
            org_id = self.kwargs['organization_pk']
            return ActivityLog.objects.filter(
                content_object__organization__id=org_id
            ).select_related('user').order_by('-timestamp')
        elif 'project_pk' in self.kwargs:
            project_id = self.kwargs['project_pk']
            return ActivityLog.objects.filter(
                content_object__project__id=project_id
            ).select_related('user').order_by('-timestamp')
        return ActivityLog.objects.none()

class ProjectMetricViewSet(viewsets.ViewSet):
    """View set for project metrics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request, project_pk=None):
        """Get all metrics for a project"""
        project = get_object_or_404(Project, id=project_pk)
        metrics = ProjectMetric.objects.filter(project=project)
        serializer = ProjectMetricSerializer(metrics, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='summary')
    def get_summary(self, request, project_pk=None):
        """Get latest metrics for a project"""
        project = get_object_or_404(Project, id=project_pk)
        metric = ProjectMetric.objects.filter(project=project).first()
        
        if not metric:
            # Return default statistics if no metrics exist
            return Response({
                'tasks_total': 0,
                'tasks_completed': 0,
                'tasks_in_progress': 0,
                'tasks_overdue': 0,
                'active_users': 0,
                'total_projects': Project.objects.count()
            })
            
        return Response({
            'tasks_total': metric.tasks_total,
            'tasks_completed': metric.tasks_completed,
            'tasks_in_progress': metric.tasks_in_progress,
            'tasks_overdue': metric.tasks_overdue,
            'active_users': metric.active_users,
            'total_projects': Project.objects.count()
        })
    
    @action(detail=False, methods=['get'], url_path='task-distribution')
    def get_task_distribution(self, request, project_pk=None):
        """Get task distribution by status"""
        project = get_object_or_404(Project, id=project_pk)
        
        # Get boards and columns for this project
        boards = project.boards.all()
        
        distribution = []
        for board in boards:
            columns = board.columns.all()
            board_data = {
                'board_name': board.name,
                'columns': []
            }
            
            for column in columns:
                column_data = {
                    'column_name': column.name,
                    'task_count': column.tasks.count()
                }
                board_data['columns'].append(column_data)
                
            distribution.append(board_data)
            
        return Response(distribution)
    
    @action(detail=False, methods=['get'], url_path='burndown')
    def get_burndown_data(self, request, project_pk=None):
        """Get burndown chart data for a project"""
        project = get_object_or_404(Project, id=project_pk)
        
        # Get date range from request parameters
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get all tasks in the project
        tasks = Task.objects.filter(column__board__project=project)
        total_tasks = tasks.count()
        
        # Calculate ideal burn rate (tasks per day)
        total_days = days
        ideal_burn_rate = total_tasks / total_days if total_days > 0 else 0
        
        # Generate daily data points
        burndown_data = []
        remaining_tasks = total_tasks
        
        # Get completed tasks by day
        done_columns = []
        for board in project.boards.all():
            done_column = board.columns.filter(name__icontains='done').first()
            if done_column:
                done_columns.append(done_column.id)
        
        if not done_columns:  # If no "done" columns found, use last column as fallback
            for board in project.boards.all():
                last_column = board.columns.order_by('-order').first()
                if last_column:
                    done_columns.append(last_column.id)
        
        # Create data points
        current_date = start_date
        while current_date <= end_date:
            # For demo purposes, simulate some completed tasks each day
            completed_tasks = Task.objects.filter(
                column_id__in=done_columns,
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
            
        return Response({
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_tasks': total_tasks,
            'burndown_data': burndown_data
        })

class UserProductivityViewSet(viewsets.ViewSet):
    """View set for user productivity metrics"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='rankings')
    def get_user_rankings(self, request, project_pk=None):
        """Get user productivity rankings"""
        project = get_object_or_404(Project, id=project_pk)
        
        # Get project members
        members = project.members.all()
        
        # Calculate activity metrics for the last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        rankings = []
        for member in members:
            user = member.user
            
            # Count tasks created
            tasks_created = Task.objects.filter(
                column__board__project=project,
                created_by=user,
                created_at__gte=thirty_days_ago
            ).count()
            
            # Count tasks completed
            try:
                done_columns = project.boards.first().columns.filter(name__icontains='done')
                tasks_completed = Task.objects.filter(
                    column__in=done_columns,
                    assignees=user,
                    updated_at__gte=thirty_days_ago
                ).count()
            except:
                tasks_completed = 0
                
            # Calculate score (simple formula for now)
            productivity_score = tasks_created + (tasks_completed * 2)
            
            rankings.append({
                'user_id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'tasks_created': tasks_created,
                'tasks_completed': tasks_completed,
                'productivity_score': productivity_score
            })
            
        # Sort by productivity score
        rankings = sorted(rankings, key=lambda x: x['productivity_score'], reverse=True)
        
        return Response(rankings)

# Add new views for recent boards and upcoming tasks
class RecentBoardsView(views.APIView):
    """API view to fetch the user's recent boards"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get recent boards for the current user"""
        user = request.user
        
        try:
            # Get boards from projects where the user is a member
            user_project_ids = user.project_memberships.values_list('project_id', flat=True)
            
            # Get recent boards (we'll use updated_at as a proxy for "recently visited")
            recent_boards = Board.objects.filter(
                project_id__in=user_project_ids
            ).order_by('-updated_at')[:5]  # Limit to 5 recent boards
            
            serializer = BoardSerializer(recent_boards, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UpcomingTasksView(views.APIView):
    """API view to fetch the user's upcoming tasks"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get upcoming tasks for the current user"""
        user = request.user
        
        try:
            # Get upcoming tasks (due in the next 7 days)
            seven_days_from_now = timezone.now() + timezone.timedelta(days=7)
            
            upcoming_tasks = Task.objects.filter(
                assignees=user,
                due_date__isnull=False,
                due_date__lte=seven_days_from_now,
                due_date__gt=timezone.now()
            ).order_by('due_date')[:10]  # Limit to 10 upcoming tasks
            
            serializer = TaskSerializer(upcoming_tasks, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
