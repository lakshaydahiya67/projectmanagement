"""
Views for editing projects and related objects.
"""
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from .models import Project, ProjectMember, Board, Column
from organizations.models import OrganizationMember

# Try to import ActivityLog model if available
try:
    from activitylogs.models import ActivityLog
    ACTIVITY_LOGS_ENABLED = True
except ImportError:
    ACTIVITY_LOGS_ENABLED = False

@login_required
def project_update_view(request, project_id):
    """
    View function for updating an existing project
    """
    # Get the project
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is a project admin
    is_project_admin = ProjectMember.objects.filter(
        project=project,
        user=request.user,
        role__in=[ProjectMember.OWNER, ProjectMember.ADMIN]
    ).exists() or request.user.is_staff
    
    if not is_project_admin:
        return render(request, 'base/error.html', {
            'message': 'You do not have permission to edit this project.'
        }, status=403)
    
    # Initialize errors dictionary
    errors = {}
    
    if request.method == 'POST':
        # Process form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        is_public = request.POST.get('is_public') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        # Validate required fields
        if not name:
            errors['name'] = 'Project name is required.'
        
        # Validate dates if provided
        if start_date and end_date:
            from datetime import datetime
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                
                if end_date_obj < start_date_obj:
                    errors['end_date'] = 'End date cannot be earlier than start date.'
            except ValueError:
                if start_date and not start_date.strip():
                    errors['start_date'] = 'Invalid start date format. Use YYYY-MM-DD.'
                if end_date and not end_date.strip():
                    errors['end_date'] = 'Invalid end date format. Use YYYY-MM-DD.'
        
        # If no errors, update the project
        if not errors:
            try:
                with transaction.atomic():
                    # Update the project
                    project.name = name
                    project.description = description
                    project.start_date = start_date if start_date else None
                    project.end_date = end_date if end_date else None
                    project.is_public = is_public
                    project.is_active = is_active
                    project.updated_at = timezone.now()
                    project.save()
                    
                    # Log the update if activity logs are enabled
                    if ACTIVITY_LOGS_ENABLED:
                        ActivityLog.objects.create(
                            user=request.user,
                            content_type=ContentType.objects.get_for_model(project),
                            object_id=str(project.id),
                            action_type=ActivityLog.UPDATED,
                            description=f"Project '{project.name}' updated"
                        )
                    
                    # Redirect to the project detail page
                    return redirect('project_detail', project_id=project.id)
            except Exception as e:
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating project: {str(e)}")
                errors['general'] = f"An error occurred while updating the project: {str(e)}"
    
    # Prepare form data for initial display
    form_data = {
        'name': project.name,
        'description': project.description,
        'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
        'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else '',
        'is_public': project.is_public,
        'is_active': project.is_active
    }
    
    # Render the project update form with any errors
    context = {
        'project': project,
        'errors': errors,
        'form_data': request.POST if request.method == 'POST' else form_data
    }
    return render(request, 'project/edit.html', context)
