"""
Security middleware for Django Project Management System
Provides rate limiting, request filtering, and security headers.
"""

import time
import hashlib
from django.http import HttpResponse, HttpResponseForbidden
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
import logging

logger = logging.getLogger(__name__)

# Custom HttpResponseTooManyRequests for older Django versions
class HttpResponseTooManyRequests(HttpResponse):
    status_code = 429


class SecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware for enhanced protection
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming requests for security validation"""
        
        # Rate limiting
        if self._is_rate_limited(request):
            logger.warning(f"Rate limit exceeded for IP: {self._get_client_ip(request)}")
            return HttpResponseTooManyRequests("Rate limit exceeded. Please try again later.")
        
        # Block suspicious requests
        if self._is_suspicious_request(request):
            logger.warning(f"Suspicious request blocked from IP: {self._get_client_ip(request)}")
            return HttpResponseForbidden("Request blocked for security reasons.")
        
        return None
    
    def process_response(self, request, response):
        """Add security headers to response"""
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        if not settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            )
            response['Content-Security-Policy'] = csp
        
        return response
    
    def _get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_rate_limited(self, request):
        """Check if request should be rate limited"""
        
        # Skip rate limiting for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return False
        
        ip = self._get_client_ip(request)
        
        # Different limits for different endpoints
        if request.path.startswith('/api/auth/'):
            # Stricter limits for auth endpoints
            limit = getattr(settings, 'AUTH_RATE_LIMIT', 5)  # 5 requests per minute
            window = 60
        elif request.path.startswith('/api/'):
            # General API rate limit
            limit = getattr(settings, 'API_RATE_LIMIT', 100)  # 100 requests per minute
            window = 60
        else:
            # Web interface rate limit
            limit = getattr(settings, 'WEB_RATE_LIMIT', 200)  # 200 requests per minute
            window = 60
        
        # Create cache key
        cache_key = f"rate_limit:{ip}:{request.path_info[:50]}"
        
        # Get current request count
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= limit:
            return True
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, window)
        return False
    
    def _is_suspicious_request(self, request):
        """Detect suspicious request patterns"""
        
        # Check for common attack patterns in URL
        suspicious_patterns = [
            '../', '..\\', '.env', 'wp-admin', 'phpinfo',
            '<script', 'javascript:', 'vbscript:', 'onload=',
            'eval(', 'exec(', '__import__', 'system(',
            'DROP TABLE', 'SELECT * FROM', 'UNION SELECT'
        ]
        
        request_data = (
            request.path.lower() + 
            request.META.get('QUERY_STRING', '').lower() +
            request.META.get('HTTP_USER_AGENT', '').lower()
        )
        
        for pattern in suspicious_patterns:
            if pattern in request_data:
                return True
        
        # Check for abnormally long URLs
        if len(request.build_absolute_uri()) > 2048:
            return True
        
        # Check for too many parameters
        if len(request.GET) > 50 or len(request.POST) > 100:
            return True
        
        return False


class APIKeyMiddleware(MiddlewareMixin):
    """
    Optional API key validation middleware for enhanced API security
    """
    
    def process_request(self, request):
        """Validate API key for API endpoints if configured"""
        
        # Only apply to API endpoints
        if not request.path.startswith('/api/'):
            return None
        
        # Skip if API key validation is disabled
        if not getattr(settings, 'REQUIRE_API_KEY', False):
            return None
        
        # Check for API key in headers
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            logger.warning(f"Missing API key from IP: {self._get_client_ip(request)}")
            return HttpResponseForbidden("API key required")
        
        # Validate API key
        valid_keys = getattr(settings, 'VALID_API_KEYS', [])
        
        if api_key not in valid_keys:
            logger.warning(f"Invalid API key from IP: {self._get_client_ip(request)}")
            return HttpResponseForbidden("Invalid API key")
        
        return None
    
    def _get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log security-relevant requests
    """
    
    def process_request(self, request):
        """Log security-relevant requests"""
        
        # Log authentication attempts
        if request.path.startswith('/api/auth/'):
            logger.info(
                f"Auth request: {request.method} {request.path} "
                f"from IP: {self._get_client_ip(request)} "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')[:100]}"
            )
        
        # Log admin access attempts
        if request.path.startswith('/admin/'):
            logger.info(
                f"Admin access: {request.method} {request.path} "
                f"from IP: {self._get_client_ip(request)} "
                f"User: {getattr(request.user, 'email', 'Anonymous')}"
            )
        
        return None
    
    def _get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
