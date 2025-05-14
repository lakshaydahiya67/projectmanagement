from django.contrib import admin
from .models import Organization, OrganizationMember, OrganizationInvitation

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__email', 'organization__name')
    date_hierarchy = 'joined_at'

@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'organization', 'role', 'invited_by', 'created_at', 'expires_at', 'accepted')
    list_filter = ('role', 'accepted', 'created_at')
    search_fields = ('email', 'organization__name', 'invited_by__email')
    date_hierarchy = 'created_at'
