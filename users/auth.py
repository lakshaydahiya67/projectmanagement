from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()

class JWTAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend that validates JWT tokens for Django views.
    This allows us to use JWT tokens for both API and template-based views.
    """
    
    def authenticate(self, request=None, token=None, **kwargs):
        if not token and request:
            # Try to get token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            
            # If no Authorization header, try to get from cookies
            if not token:
                token = request.COOKIES.get('access_token')
                
            # If still no token, try to get from session
            if not token:
                token = request.session.get('access_token')
        
        if not token:
            return None
            
        try:
            # Use SimpleJWT's JWTAuthentication to validate the token
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            return user
        except (InvalidToken, TokenError):
            return None
