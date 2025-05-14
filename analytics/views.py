from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from datetime import datetime, timedelta
from django_filters.rest_framework import DjangoFilterBackend

from projects.permissions import IsProjectMember, IsProjectAdmin
from organizations.permissions import IsOrganizationMember, IsOrganizationAdmin
from .models import ActivityLog, ProjectMetric, UserProductivity
from .serializers import ActivityLogSerializer, ProjectMetricSerializer, UserProductivitySerializer

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for activity logs
    """
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action_type', 'entity_type', 'user', 'project']
    search_fields = ['entity_name']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        organization_id = self.kwargs.get('organization_pk')
        return ActivityLog.objects.filter(organization_id=organization_id)

class ProjectMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for project metrics
    """
    serializer_class = ProjectMetricSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date']
    ordering = ['-date']
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        return ProjectMetric.objects.filter(project_id=project_id)
    
    @action(detail=False, methods=['get'])
    def summary(self, request, project_pk=None):
        """Get a summary of key project metrics"""
        # Get date range from query params or default to last 30 days
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get metrics for the date range
        metrics = ProjectMetric.objects.filter(
            project_id=project_pk,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Calculate summary metrics
        total_tasks = metrics.aggregate(Sum('tasks_total'))['tasks_total__sum'] or 0
        total_tasks_completed = metrics.aggregate(Sum('tasks_completed'))['tasks_completed__sum'] or 0
        total_tasks_overdue = metrics.aggregate(Sum('tasks_overdue'))['tasks_overdue__sum'] or 0
        avg_active_users = metrics.aggregate(Avg('active_users'))['active_users__avg'] or 0
        
        # Format for chart data
        chart_data = {
            'labels': [metric.date.strftime('%Y-%m-%d') for metric in metrics],
            'tasks_total': [metric.tasks_total for metric in metrics],
            'tasks_completed': [metric.tasks_completed for metric in metrics],
            'tasks_overdue': [metric.tasks_overdue for metric in metrics],
            'active_users': [metric.active_users for metric in metrics],
        }
        
        return Response({
            'summary': {
                'total_tasks': total_tasks,
                'total_tasks_completed': total_tasks_completed,
                'total_tasks_overdue': total_tasks_overdue,
                'avg_active_users': round(avg_active_users, 2),
                'completion_rate': round((total_tasks_completed / total_tasks) * 100, 2) if total_tasks > 0 else 0,
            },
            'chart_data': chart_data
        })
    
    @action(detail=False, methods=['get'])
    def burndown(self, request, project_pk=None):
        """Get data for a burndown chart"""
        # Get date range from query params or default to last 30 days
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get metrics for the date range
        metrics = ProjectMetric.objects.filter(
            project_id=project_pk,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Calculate cumulative metrics for burndown chart
        burndown_data = []
        total_tasks = metrics.first().tasks_total if metrics.exists() else 0
        remaining_tasks = total_tasks
        
        for metric in metrics:
            remaining_tasks -= metric.tasks_completed
            burndown_data.append({
                'date': metric.date.strftime('%Y-%m-%d'),
                'remaining_tasks': remaining_tasks,
                'ideal_remaining': total_tasks - ((total_tasks / len(metrics)) * (metrics.index(metric) + 1))
            })
        
        return Response({
            'total_tasks': total_tasks,
            'burndown_data': burndown_data
        })

class UserProductivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user productivity metrics
    """
    serializer_class = UserProductivitySerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'date']
    ordering_fields = ['date', 'tasks_completed']
    ordering = ['-date']
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        return UserProductivity.objects.filter(project_id=project_id)
    
    @action(detail=False, methods=['get'])
    def rankings(self, request, project_pk=None):
        """Get user productivity rankings"""
        # Get date range from query params or default to last 30 days
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get metrics for all users in this period
        metrics = UserProductivity.objects.filter(
            project_id=project_pk,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Aggregate by user
        user_metrics = metrics.values('user', 'user__first_name', 'user__last_name').annotate(
            total_tasks_completed=Sum('tasks_completed'),
            total_tasks_created=Sum('tasks_created'),
            total_comments=Sum('comments_created'),
            total_activity=Sum('total_activity')
        ).order_by('-total_tasks_completed')
        
        return Response(user_metrics)
