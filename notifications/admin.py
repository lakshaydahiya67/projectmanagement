from django.contrib import admin
from .models import Notification, NotificationSetting

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'created_at', 'read')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('recipient__email', 'title', 'message')
    date_hierarchy = 'created_at'

@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'task_assigned', 'deadline_approaching', 'comment_added')
    list_filter = ('task_assigned', 'deadline_approaching', 'comment_added')
    search_fields = ('user__email',)
