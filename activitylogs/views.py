from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
import django_filters

from .models import ActivityLog
from .serializers import ActivityLogSerializer
from organizations.permissions import IsOrgMemberReadOnly

class ActivityLogFilter(django_filters.FilterSet):
    """Filter for activity logs"""
    start_date = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    user = django_filters.UUIDFilter(field_name='user__id')
    # Named 'project' to match the frontend parameter, but filters on 'project_id' field
    project = django_filters.UUIDFilter(field_name='project_id')
    action_type = django_filters.CharFilter(field_name='action_type')
    content_type = django_filters.CharFilter(field_name='content_type__model')
    
    # Shortcut filters for time periods
    last_day = django_filters.BooleanFilter(method='filter_last_day')
    last_week = django_filters.BooleanFilter(method='filter_last_week')
    last_month = django_filters.BooleanFilter(method='filter_last_month')
    
    def filter_last_day(self, queryset, name, value):
        if value:
            yesterday = timezone.now() - timedelta(days=1)
            return queryset.filter(timestamp__gte=yesterday)
        return queryset
    
    def filter_last_week(self, queryset, name, value):
        if value:
            last_week = timezone.now() - timedelta(days=7)
            return queryset.filter(timestamp__gte=last_week)
        return queryset
    
    def filter_last_month(self, queryset, name, value):
        if value:
            last_month = timezone.now() - timedelta(days=30)
            return queryset.filter(timestamp__gte=last_month)
        return queryset
    
    class Meta:
        model = ActivityLog
        fields = ['user', 'action_type', 'project', 'content_type', 'start_date', 'end_date']

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing activity logs
    """
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, IsOrgMemberReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ActivityLogFilter
    search_fields = ['description']
    ordering_fields = ['timestamp', 'action_type', 'user__username']
    ordering = ['-timestamp']  # Default ordering
    
    def get_queryset(self):
        user = self.request.user
        
        # If the user is a superuser, they can see all activity logs
        if user.is_superuser:
            return ActivityLog.objects.all()
        
        # Otherwise, users can only see activity logs for projects they are a member of
        # Get all projects the user is a member of
        from projects.models import ProjectMember
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        
        return ActivityLog.objects.filter(project_id__in=project_ids) 