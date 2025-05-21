import logging
from functools import wraps
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.urls import resolve, Resolver404
from django.http import HttpResponse

logger = logging.getLogger(__name__)

def jwt_login_required(function=None, redirect_url='/login/'):
    """
    Decorator for views that checks that the user is authenticated using JWT,
    redirecting to the log-in page if necessary.
    
    This is a replacement for Django's built-in login_required decorator
    that works with JWT authentication instead of session-based auth.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Special case for logout requests and complete-logout - always allow them through
            if request.path.endswith('/logout/') or request.path.endswith('/token/logout/') or 'logout' in request.path.lower():
                logger.debug(f"Allowing logout request through without authentication check: {request.path}")
                return view_func(request, *args, **kwargs)
                
            # Enhanced check for login page and related paths to prevent redirect loops
            if request.path.startswith(redirect_url) or request.path.endswith('/login/') or '/login' in request.path:
                logger.debug(f"Login-related page detected, allowing through: {request.path}")
                return view_func(request, *args, **kwargs)
                
            # Also check URL parameters for logout indicators
            if request.GET.get('clean_logout') or request.GET.get('force_logout') or request.GET.get('complete_logout'):
                logger.debug(f"Logout indicator in query params, allowing through: {request.path}")
                return view_func(request, *args, **kwargs)
                
            # Check for named URL as a fallback
            try:
                current_url_name = resolve(request.path).url_name
                if current_url_name == 'login':
                    logger.debug(f"Login URL name detected, allowing through: {request.path}")
                    return view_func(request, *args, **kwargs)
            except Resolver404:
                pass  # Not a named URL, continue with normal flow
                
            # Check if user is authenticated (should be set by JWTAuthenticationMiddleware)
            if request.user.is_authenticated:
                logger.debug(f"User authenticated: {request.user.username}, proceeding with view")
                return view_func(request, *args, **kwargs)
            else:
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    logger.debug("AJAX request detected, returning 401 instead of redirect")
                    return HttpResponse(status=401)
                    
                # Check for recent logout via cookie or session
                import time
                current_time = int(time.time())
                logout_timestamp_cookie = request.COOKIES.get('logout_timestamp')
                
                # Also check session for logout indicators
                logout_timestamp_session = None
                force_logout = False
                if hasattr(request, 'session'):
                    logout_timestamp_session = request.session.get('logout_timestamp')
                    force_logout = request.session.get('force_logout') == 'true'
                
                # Check for recent logout via cookie or session
                recent_logout = False
                if logout_timestamp_cookie and (current_time - int(logout_timestamp_cookie)) < 300:  # 5 minutes
                    recent_logout = True
                    logger.debug(f"Recent logout detected from cookie timestamp: {logout_timestamp_cookie}")
                    # CRITICAL FIX: Completely remove the Authorization header when a logout is detected
                    if 'HTTP_AUTHORIZATION' in request.META:
                        del request.META['HTTP_AUTHORIZATION']
                        logger.debug("Removed Authorization header due to recent logout")
                elif logout_timestamp_session and (current_time - int(logout_timestamp_session)) < 300:
                    recent_logout = True
                    logger.debug(f"Recent logout detected from session timestamp: {logout_timestamp_session}")
                    # CRITICAL FIX: Completely remove the Authorization header when a logout is detected
                    if 'HTTP_AUTHORIZATION' in request.META:
                        del request.META['HTTP_AUTHORIZATION']
                        logger.debug("Removed Authorization header due to recent logout")
                elif force_logout:
                    recent_logout = True
                    logger.debug("Force logout flag detected in session")
                    # CRITICAL FIX: Completely remove the Authorization header when a logout is detected
                    if 'HTTP_AUTHORIZATION' in request.META:
                        del request.META['HTTP_AUTHORIZATION']
                        logger.debug("Removed Authorization header due to force logout")
                elif request.headers.get('X-Auth-Cleared') == 'true' or request.headers.get('X-Force-Logout') == 'true':
                    recent_logout = True
                    logger.debug("Logout header detected in request")
                    # CRITICAL FIX: Completely remove the Authorization header when a logout is detected
                    if 'HTTP_AUTHORIZATION' in request.META:
                        del request.META['HTTP_AUTHORIZATION']
                        logger.debug("Removed Authorization header due to logout header")
                
                # Add debugging information to help identify the issue
                logger.debug(f"User not authenticated, redirecting to {redirect_url}")
                auth_header = request.META.get('HTTP_AUTHORIZATION', 'None')
                has_cookie = 'access_token' in request.COOKIES
                logger.debug(f"Auth header exists: {bool(auth_header)}, Has cookie: {has_cookie}")
                
                # Add cache-busting parameter to prevent browser caching
                cache_buster = current_time
                
                # Redirect to login page - only add next parameter if not a recent logout
                if recent_logout:
                    # Use a more explicit URL to prevent any redirection loops
                    return redirect(f"{redirect_url}?clean_logout=true&force_logout=true&t={cache_buster}")
                else:
                    return redirect(f"{redirect_url}?next={request.path}&t={cache_buster}")
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator

# Class-based view decorator
def class_jwt_login_required(cls):
    """
    Decorator for class-based views that checks for JWT authentication.
    Applies jwt_login_required to all handler methods.
    """
    for name, method in cls.__dict__.items():
        # Check if it's a handler method
        if name.lower() in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'):
            setattr(cls, name, method_decorator(jwt_login_required)(method))
    return cls
