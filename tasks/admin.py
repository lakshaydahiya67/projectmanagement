from django.contrib import admin
from .models import Label, Task, Comment, Attachment

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'project')
    list_filter = ('project',)
    search_fields = ('name', 'project__name')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'column', 'priority', 'due_date', 'created_by', 'is_overdue')
    list_filter = ('priority', 'column__board__project', 'column')
    search_fields = ('title', 'description')
    filter_horizontal = ('labels', 'assignees')
    readonly_fields = ('created_at', 'updated_at', 'is_overdue')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'column', 'order')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'due_date')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assignees', 'labels', 'priority')
        }),
        ('Effort', {
            'fields': ('estimated_hours', 'actual_hours')
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'task', 'created_at', 'updated_at')
    list_filter = ('task__column__board__project', 'author')
    search_fields = ('content', 'author__username', 'task__title')
    readonly_fields = ('created_at', 'updated_at')
    
@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'task', 'uploaded_by', 'uploaded_at', 'file_size')
    list_filter = ('task__column__board__project', 'uploaded_by')
    search_fields = ('filename', 'task__title')
    readonly_fields = ('uploaded_at', 'file_size')
