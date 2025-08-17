from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, FileResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import time
import os
from rest_framework import status
from projects.models import Project, ProjectMember
from organizations.models import Organization, OrganizationMember
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
from activitylogs.models import ActivityLog
from tasks.models import Task
from django.utils import timezone
from django.db.models import Q
import json

logger = logging.getLogger(__name__)

@login_required
def dashboard_view(request):
    """
    View function for rendering the dashboard page with initial data
    """
    # Get organizations the user is a member of
    user_organizations = Organization.objects.filter(
        members__user=request.user
    ).distinct()
    
    # Get projects the user is a member of
    user_projects = Project.objects.filter(
        members__user=request.user
    ).select_related('organization').order_by('-created_at')[:10]
    
    # Get recent activity (limited to 10 items)
    try:
        recent_activity = ActivityLog.objects.filter(
            Q(organization__in=user_organizations) |
            Q(project__in=user_projects)
        ).select_related('user', 'content_type').order_by('-timestamp')[:10]
    except:
        # ActivityLog might not be available or accessible
        recent_activity = []
    
    # Get upcoming tasks (limited to 5 items)
    try:
        today = timezone.now().date()
        upcoming_tasks = Task.objects.filter(
            assignees=request.user,
            due_date__gte=today
        ).order_by('due_date')[:5]
    except:
        # Tasks might not be properly configured
        upcoming_tasks = []
    
    context = {
        'organizations': user_organizations,
        'projects': user_projects,
        'recent_activity': recent_activity,
        'upcoming_tasks': upcoming_tasks
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile_view(request):
    """
    View function for rendering the user profile page
    """
    # The @login_required decorator ensures request.user is available
    return render(request, 'user/profile.html', {'user': request.user})


@ensure_csrf_cookie
def activation_view(request, uid, token):
    """
    View function for handling user account activation
    
    This view renders a template that will automatically submit the activation
    request to Djoser's activation endpoint via JavaScript
    """
    context = {
        'uid': uid,
        'token': token
    }
    return render(request, 'auth/activation.html', context)


@require_POST
def logout_view(request):
    """
    Simple logout view for session-based authentication
    """
    logger.debug(f"Logout request received from {request.META.get('REMOTE_ADDR')}")
    
    # Django's built-in logout
    logout(request)
    
    return JsonResponse({'detail': 'Logout successful'}, status=status.HTTP_200_OK)


# complete_logout removed - not needed for session authentication


@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def serve_service_worker(request):
    """
    Serve the service worker file with the correct Service-Worker-Allowed header
    """
    # First check for the service worker at the root (preferred location)
    root_file_path = os.path.join(settings.BASE_DIR, 'auth-service-worker.js')
    
    if os.path.exists(root_file_path):
        logger.info(f"Serving service worker from root directory: {root_file_path}")
        file_path = root_file_path
    else:
        # Fall back to the static directory locations
        file_path = os.path.join(settings.STATIC_ROOT, 'js', 'auth-service-worker.js')
        if not os.path.exists(file_path):
            # Fall back to the static files directory in the project
            file_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'auth-service-worker.js')
            logger.info(f"Serving service worker from static directory: {file_path}")
    
    # Create a response with the file content
    response = FileResponse(open(file_path, 'rb'), content_type='application/javascript')
    
    # Add the Service-Worker-Allowed header
    response['Service-Worker-Allowed'] = '/'
    
    # Log that we're serving the service worker
    logger.info(f"Serving service worker with Service-Worker-Allowed header from {file_path}")
    
    return response
