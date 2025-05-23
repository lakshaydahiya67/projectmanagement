"""
Views that are completely public and bypass all authentication.
These views are designed to be used for endpoints that should be accessible without any authentication.
"""

import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .email import send_password_reset_email

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def public_password_reset(request):
    """
    Public password reset view that completely bypasses authentication.
    This is a dedicated endpoint for password reset that doesn't require any authentication.
    """
    # Log the request for debugging
    logger.info(f"Public password reset request received for: {request.data.get('email', 'unknown')}"
               f" from {request.META.get('REMOTE_ADDR')}")
    
    email = request.data.get('email', '')
    if not email:
        return Response({"detail": "Email is required."}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Find the user by email
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(email=email)
        logger.info(f"Found user with email {email}")
    except UserModel.DoesNotExist:
        # For security reasons, don't reveal that the user doesn't exist
        logger.info(f"No user found with email {email}")
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # Generate password reset token
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Create reset URL
    domain = settings.DJOSER.get('DOMAIN')
    protocol = 'https' if settings.DJOSER.get('USE_HTTPS', False) else 'http'
    url_template = settings.DJOSER.get('PASSWORD_RESET_CONFIRM_URL')
    reset_url = f"{protocol}://{domain}/{url_template.format(uid=uid, token=token)}"
    
    logger.info(f"Generated reset URL: {reset_url}")
    
    try:
        # Send password reset email using our custom function
        result = send_password_reset_email(user, reset_url)
        
        if result:
            logger.info(f"Password reset email sent successfully to {email}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            logger.error(f"Failed to send password reset email to {email}")
            return Response({"detail": "Failed to send password reset email."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception(f"Error sending password reset email: {str(e)}")
        return Response({"detail": "An error occurred while sending the password reset email."}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
