import logging
import time
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

logger = logging.getLogger(__name__)

def get_user_from_request(request):
    """
    Extract and validate JWT token from request, then return the corresponding user
    """
    # Skip JWT authentication for admin paths and public endpoints
    if request.path.startswith('/admin/') or \
       request.path.endswith('/password-reset/') or \
       'reset_password' in request.path or \
       'forgot-password' in request.path:
        logger.debug(f"Public path detected: {request.path}, skipping JWT authentication")
        # Return AnonymousUser to ensure the request continues without authentication
        return AnonymousUser()
        
    # Multi-layered logout detection - check multiple sources to ensure we detect logout state
    
    # 1. Check for recent logout via cookie
    logout_timestamp_cookie = request.COOKIES.get('logout_timestamp')
    
    # 2. Check for recent logout via session
    logout_timestamp_session = None
    force_logout = False
    if hasattr(request, 'session'):
        logout_timestamp_session = request.session.get('logout_timestamp')
        force_logout = request.session.get('force_logout') == 'true'
    
    # 3. Check for logout via request headers
    logout_header = request.META.get('HTTP_X_LOGOUT_TIMESTAMP')
    
    current_time = int(time.time())
    logout_detected = False
    
    # Check all sources with detailed logging
    if logout_timestamp_cookie and (current_time - int(logout_timestamp_cookie)) < 120:
        logger.debug(f"Recent logout detected from cookie timestamp: {logout_timestamp_cookie}, returning AnonymousUser")
        logout_detected = True
    elif logout_timestamp_session and (current_time - int(logout_timestamp_session)) < 120:
        logger.debug(f"Recent logout detected from session timestamp: {logout_timestamp_session}, returning AnonymousUser")
        logout_detected = True
    elif logout_header and (current_time - int(logout_header)) < 120:
        logger.debug(f"Recent logout detected from header timestamp: {logout_header}, returning AnonymousUser")
        logout_detected = True
    elif force_logout:
        logger.debug("Force logout flag detected in session, returning AnonymousUser")
        logout_detected = True
    
    if logout_detected:
        request._jwt_user_cached = AnonymousUser()
        return request._jwt_user_cached
        
    # Check for logout path - always return AnonymousUser for logout requests
    if request.path.endswith('/logout/') or request.path.endswith('/token/logout/') or 'logout' in request.path.lower():
        logger.debug(f"Logout path detected: {request.path}, returning AnonymousUser")
        request._jwt_user_cached = AnonymousUser()
        return request._jwt_user_cached
        
    # Check for login page - if we're on login page, user should be anonymous
    if (request.path.endswith('/login/') or request.path == '/login') and not request.path.startswith('/admin/'):
        logger.debug(f"Login page detected: {request.path}, returning AnonymousUser")
        # Remove any Authorization header to prevent authentication attempts on login page
        if 'HTTP_AUTHORIZATION' in request.META:
            del request.META['HTTP_AUTHORIZATION']
            logger.debug("Removed Authorization header on login page")
        # Clear any cached authentication
        if hasattr(request, '_jwt_user_cached'):
            delattr(request, '_jwt_user_cached')
        request._jwt_user_cached = AnonymousUser()
        return request._jwt_user_cached
    
    # First check if this is a recent logout before processing any tokens
    logout_timestamp_cookie = request.COOKIES.get('logout_timestamp')
    logout_timestamp_session = None
    force_logout = False
    if hasattr(request, 'session'):
        logout_timestamp_session = request.session.get('logout_timestamp')
        force_logout = request.session.get('force_logout') == 'true'
    
    # If we detect a recent logout, don't process any tokens and block Authorization headers
    logout_detected = False
    
    # Check all possible logout indicators
    if logout_timestamp_cookie and (current_time - int(logout_timestamp_cookie)) < 300:  # 5 minutes
        logger.debug(f"Recent logout detected from cookie timestamp: {logout_timestamp_cookie}")
        logout_detected = True
    elif logout_timestamp_session and (current_time - int(logout_timestamp_session)) < 300:
        logger.debug(f"Recent logout detected from session timestamp: {logout_timestamp_session}")
        logout_detected = True
    elif force_logout:
        logger.debug("Force logout flag detected in session")
        logout_detected = True
    elif request.headers.get('X-Auth-Cleared') == 'true' or request.headers.get('X-Force-Logout') == 'true':
        logger.debug("Logout header detected in request")
        logout_detected = True
    elif 'clean_logout' in request.GET or 'force_logout' in request.GET:
        logger.debug("Logout parameter detected in query string")
        logout_detected = True
    
    if logout_detected:
        # CRITICAL FIX: Completely remove the Authorization header
        if 'HTTP_AUTHORIZATION' in request.META:
            del request.META['HTTP_AUTHORIZATION']
            logger.debug("Removed Authorization header due to logout detection")
        
        # Also clear any token from cookies and session to be thorough
        if 'access_token' in request.COOKIES:
            # We can't modify cookies here, but we can prevent them from being used
            logger.debug("Ignoring access_token cookie due to logout detection")
        
        if hasattr(request, 'session') and 'access_token' in request.session:
            del request.session['access_token']
            logger.debug("Removed access_token from session due to logout detection")
        
        request._jwt_user_cached = AnonymousUser()
        return request._jwt_user_cached
    
    # Try to get token from Authorization header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = None
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        logger.debug("Found token in Authorization header")
    
    # If no token in header, try cookies
    if not token:
        token = request.COOKIES.get('access_token')
        if token:
            logger.debug("Found token in cookies")
    
    # If still no token, try session (as a fallback mechanism)
    if not token and hasattr(request, 'session'):
        token = request.session.get('access_token')
        if token:
            logger.debug("Found token in session")
    
    # If token found, authenticate - but with extra validation checks
    if token:
        try:
            # First, check if this is a logout request or we're on a login page
            # In these cases, we should be extra cautious about validating tokens
            is_sensitive_path = False
            if 'logout' in request.path.lower() or '/login/' in request.path:
                is_sensitive_path = True
                logger.debug(f"Sensitive path detected: {request.path}, applying stricter token validation")
            
            # Check for session-based logout indicator
            if hasattr(request, 'session') and request.session.get('force_logout') == 'true':
                logger.debug("Force logout flag in session, rejecting token")
                request._jwt_user_cached = AnonymousUser()
                return request._jwt_user_cached
            
            # Proceed with normal JWT validation
            jwt_auth = JWTAuthentication()
            
            # Try to decode the token first without full validation to check expiry
            try:
                from rest_framework_simplejwt.tokens import UntypedToken
                raw_token = UntypedToken(token)
                
                # Check if token is about to expire (within 30 seconds)
                exp = raw_token.get('exp', 0)
                if exp and (exp - current_time) < 30:
                    logger.warning(f"Token is about to expire, rejecting: exp={exp}, now={current_time}")
                    request._jwt_user_cached = AnonymousUser()
                    return request._jwt_user_cached
                    
                # Check token type - if we're logging out, be strict about token types
                token_type = raw_token.get('token_type', '')
                if is_sensitive_path and token_type != 'access':
                    logger.warning(f"Non-access token used for sensitive path: {token_type}")
                    request._jwt_user_cached = AnonymousUser()
                    return request._jwt_user_cached
            except Exception as e:
                logger.warning(f"Error pre-validating token: {str(e)}")
                if is_sensitive_path:
                    request._jwt_user_cached = AnonymousUser()
                    return request._jwt_user_cached
            
            # Full token validation
            validated_token = jwt_auth.get_validated_token(token)
            
            # Check if token is blacklisted
            try:
                jti = validated_token.get('jti')
                if jti and BlacklistedToken.objects.filter(token__jti=jti).exists():
                    logger.warning(f"Token is blacklisted: {jti}")
                    request._jwt_user_cached = AnonymousUser()
                    return request._jwt_user_cached
            except Exception as e:
                logger.warning(f"Error checking blacklist: {str(e)}")
                if is_sensitive_path:
                    request._jwt_user_cached = AnonymousUser()
                    return request._jwt_user_cached
            
            # Get the user from the token
            user = jwt_auth.get_user(validated_token)
            if not user or not user.is_active:
                logger.warning(f"User not found or inactive for token")
                request._jwt_user_cached = AnonymousUser()
                return request._jwt_user_cached
                
            request._jwt_user_cached = user
            logger.debug(f"Successfully authenticated user: {user.username if user else 'None'}")
            return user
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Token validation error: {str(e)}")
            request._jwt_user_cached = AnonymousUser()
            return request._jwt_user_cached
    
    # No token found
    logger.debug("No valid token found, returning AnonymousUser")
    request._jwt_user_cached = AnonymousUser()
    return request._jwt_user_cached

class JWTAuthenticationMiddleware:
    """
    Middleware that authenticates users via JWT tokens for all HTTP requests
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip JWT authentication for admin paths and public endpoints
        if request.path.startswith('/admin/') or \
           request.path.endswith('/password-reset/') or \
           'reset_password' in request.path or \
           'forgot-password' in request.path:
            # Let Django's built-in auth middleware handle admin authentication
            # and allow public access to password reset endpoints
            logger.debug(f"Public path detected in middleware: {request.path}, bypassing JWT authentication")
            return self.get_response(request)
            
        # Clear any cached authentication for this request
        if hasattr(request, '_jwt_user_cached'):
            delattr(request, '_jwt_user_cached')
            
        # Add JWT user to request
        request.user = SimpleLazyObject(lambda: get_user_from_request(request))
        
        # Continue with the request
        response = self.get_response(request)
        
        # For logout requests, ensure we clear any auth cookies in the response
        if request.path.endswith('/logout/') or request.path.endswith('/token/logout/') or 'logout' in request.path.lower():
            current_time = int(time.time())
            max_age = 300  # 5 minutes
            
            # Define paths and domains to clear cookies from
            cookie_names = ['access_token', 'refresh_token', 'csrftoken', 'sessionid', 'jwt', 'token']
            paths = ['/', '/api/', '/api/v1/', '/auth/', '/dashboard/', '/admin/', '']
            domains = [None, '', request.get_host(), 'localhost', '127.0.0.1']
            
            # Add headers to explicitly clear Authorization header at the browser level
            # This is critical for preventing the browser from sending the header with future requests
            response['Clear-Site-Data'] = '"cache", "cookies", "storage"'  # Clear all site data
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            # Add custom headers to signal client-side code to clear auth headers
            response['X-Clear-Authorization'] = 'true'
            response['X-Logout-Timestamp'] = str(current_time)
            
            # First set the logout timestamp cookie - this is critical for tracking logout state
            # Set it with multiple approaches to ensure it's properly set
            
            # 1. Set it directly in the response
            response.set_cookie(
                'logout_timestamp',
                value=str(current_time),
                max_age=max_age,
                path='/',
                httponly=True
            )
            
            # 2. Also set it as a session cookie
            if hasattr(request, 'session'):
                request.session['logout_timestamp'] = str(current_time)
                request.session['force_logout'] = 'true'
                request.session.modified = True
                
            # 3. Add it to response headers for good measure
            response['X-Logout-Timestamp'] = str(current_time)
            
            # Then clear all authentication cookies
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
            
            # Set cache control headers
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            logger.debug(f"Set logout timestamp cookie to {current_time} and cleared all auth cookies in middleware response")
            
        return response
