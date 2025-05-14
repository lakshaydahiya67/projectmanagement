from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'content_type', 'timestamp', 'description')
    list_filter = ('action_type', 'content_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'description')
    readonly_fields = ('user', 'action_type', 'content_type', 'object_id', 'timestamp', 'description', 'metadata', 'ip_address', 'project_id')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Activity logs should only be created through the system, not manually
        return False
    
    def has_change_permission(self, request, obj=None):
        # Activity logs should not be modified
        return False 