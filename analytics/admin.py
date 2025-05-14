from django.contrib import admin
from .models import ActivityLog, ProjectMetric, UserProductivity

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'entity_type', 'entity_name', 'timestamp')
    list_filter = ('action_type', 'entity_type', 'timestamp')
    search_fields = ('user__username', 'entity_name')
    readonly_fields = ('user', 'organization', 'project', 'action_type', 'entity_type',
                     'entity_id', 'entity_name', 'details', 'timestamp')
    date_hierarchy = 'timestamp'

@admin.register(ProjectMetric)
class ProjectMetricAdmin(admin.ModelAdmin):
    list_display = ('project', 'date', 'tasks_total', 'tasks_completed', 'tasks_overdue', 'active_users')
    list_filter = ('date', 'project')
    date_hierarchy = 'date'

@admin.register(UserProductivity)
class UserProductivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'date', 'tasks_completed', 'tasks_created', 'comments_created', 'total_activity')
    list_filter = ('date', 'project', 'user')
    search_fields = ('user__username', 'project__name')
    date_hierarchy = 'date'
