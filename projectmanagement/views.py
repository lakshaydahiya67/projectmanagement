from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, FileResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_control
from rest_framework_simplejwt.tokens import RefreshToken
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
from users.decorators import jwt_login_required
import json
import logging

logger = logging.getLogger(__name__)

@jwt_login_required
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


@jwt_login_required
def profile_view(request):
    """
    View function for rendering the user profile page
    """
    # The @jwt_login_required decorator ensures request.user is available
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
    Custom view to handle JWT token blacklisting during logout
    
    This correctly invalidates the refresh token on the server side to ensure
    full security during logout, preventing token reuse
    """
    # Log the request details for debugging
    logger.debug(f"Logout request received from {request.META.get('REMOTE_ADDR')}")
    logger.debug(f"User agent: {request.META.get('HTTP_USER_AGENT')}")
    logger.debug(f"Referrer: {request.META.get('HTTP_REFERER')}")
    
    # Create response object early so we can add cookies regardless of path
    response = JsonResponse({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
    
    # Force logout by setting session flag
    if hasattr(request, 'session'):
        request.session['force_logout'] = 'true'
        request.session['logout_timestamp'] = str(int(time.time()))
        request.session.modified = True
        logger.debug("Set force_logout flag in session")
        
    # Add logout timestamp to response headers
    response['X-Logout-Timestamp'] = str(int(time.time()))
    response['X-Force-Logout'] = 'true'
    
    # Always clear all cookies first regardless of what happens next
    # Use a more comprehensive list of cookies and paths
    cookie_names = ['access_token', 'refresh_token', 'csrftoken', 'sessionid', 'jwt', 'token']
    paths = ['/', '/api/', '/api/v1/', '/auth/', '/dashboard/', '/admin/', '']
    domains = [None, '', request.get_host(), 'localhost', '127.0.0.1']
    
    # Systematically clear all cookies with all possible combinations
    for cookie_name in cookie_names:
        # First try with all path and domain combinations
        for path in paths:
            for domain in domains:
                # Try with different SameSite settings
                response.delete_cookie(cookie_name, path=path, domain=domain, samesite='Lax')
                response.delete_cookie(cookie_name, path=path, domain=domain, samesite='Strict')
                response.delete_cookie(cookie_name, path=path, domain=domain, samesite='None')
                
                # Also try without SameSite
                response.delete_cookie(cookie_name, path=path, domain=domain)
        
        # Also try without path specification
        for domain in domains:
            response.delete_cookie(cookie_name, domain=domain)
        
        # And finally try with just the name
        response.delete_cookie(cookie_name)
    
    # Ensure cache control headers are set to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


@csrf_exempt
@require_POST
def complete_logout(request):
    """
    Final step in the logout process - handles the form submission from client
    and ensures a clean redirect to the login page
    """
    logger.info("Complete logout endpoint called")
    
    # Get the timestamp from the request
    timestamp = request.POST.get('timestamp', str(int(time.time())))
    
    # Create response that redirects to login page with clean_logout parameter
    # This ensures no 'next' parameter is added which would cause redirect loops
    response = HttpResponseRedirect(f'/login/?clean_logout=true&t={timestamp}&force_logout=true')
    
    # Set force logout in session
    if hasattr(request, 'session'):
        request.session['force_logout'] = 'true'
        request.session['logout_timestamp'] = timestamp
        request.session.modified = True
        logger.debug("Set force_logout flag in session during complete-logout")
    
    # Add logout timestamp to response headers
    response['X-Logout-Timestamp'] = timestamp
    response['X-Force-Logout'] = 'true'
    
    # Clear all cookies
    cookie_names = ['access_token', 'refresh_token', 'csrftoken', 'sessionid', 'jwt', 'token']
    paths = ['/', '/api/', '/api/v1/', '/auth/', '/dashboard/', '/admin/', '']
    domains = [None, '', request.get_host(), 'localhost', '127.0.0.1']
    
    # Set logout timestamp cookie
    response.set_cookie(
        'logout_timestamp',
        value=timestamp,
        max_age=300,  # 5 minutes
        path='/',
        httponly=True
    )
    
    # Clear all authentication cookies
    for cookie_name in cookie_names:
        for path in paths:
            for domain in domains:
                try:
                    response.delete_cookie(cookie_name, path=path, domain=domain)
                except Exception as e:
                    logger.error(f"Error clearing cookie {cookie_name} on path {path} domain {domain}: {str(e)}")
    
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    logger.debug(f"Complete-logout request completed successfully")
    return response


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
