"""
Utility functions for the projectmanagement application.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that provides better error messages
    and logging for authentication errors.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If this is an authentication error, log it and provide a more helpful message
    if response is not None and response.status_code == status.HTTP_401_UNAUTHORIZED:
        request = context.get('request')
        view = context.get('view')
        
        # Log detailed information about the request
        logger.warning(
            f"Authentication error in {view.__class__.__name__} for {request.method} {request.path}. "
            f"Auth headers present: {bool(request.headers.get('Authorization'))}. "
            f"User: {request.user}"
        )
        
        # Check if this is likely a token issue
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            # This looks like a token issue, provide a helpful message
            response.data = {
                'detail': 'Authentication credentials are invalid or expired. Please log in again.',
                'code': 'token_invalid',
            }
        
    return response
