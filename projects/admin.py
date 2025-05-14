from django.contrib import admin
import sys
print("Python path:", sys.path)
print("Attempting to import from .models...")
from .models import Project, ProjectMember, Board, Column, BoardViewer

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'created_by', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'organization', 'start_date')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__email', 'project__name')
    date_hierarchy = 'joined_at'

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_by', 'is_default')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name', 'description', 'project__name')
    date_hierarchy = 'created_at'

@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ('name', 'board', 'order', 'wip_limit')
    list_filter = ('board__project', 'created_at')
    search_fields = ('name', 'board__name')
    ordering = ('board', 'order')

@admin.register(BoardViewer)
class BoardViewerAdmin(admin.ModelAdmin):
    list_display = ('user', 'board', 'joined_at', 'last_activity')
    list_filter = ('joined_at', 'last_activity')
    search_fields = ('user__email', 'board__name')
    date_hierarchy = 'last_activity'
