"""
Custom JWT views to handle remember_me functionality for dynamic token lifetimes.
"""
from datetime import timedelta
from django.conf import settings
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer that extends the default TokenObtainPairSerializer
    to handle the remember_me parameter for dynamic token lifetimes.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add remember_me field to the serializer
        self.fields['remember_me'] = serializers.BooleanField(required=False, default=False)
    
    def validate(self, attrs):
        # Get the remember_me value before calling parent validation
        remember_me = attrs.pop('remember_me', False)
        
        # Call parent validation to get the token data
        data = super().validate(attrs)
        
        # Get the refresh token from the response
        refresh = self.get_token(self.user)
        
        # Adjust token lifetimes based on remember_me parameter
        if remember_me:
            # Extended lifetimes for "remember me" option
            access_lifetime = getattr(settings, 'SIMPLE_JWT_REMEMBER_ACCESS_TOKEN_LIFETIME', timedelta(days=1))
            refresh_lifetime = getattr(settings, 'SIMPLE_JWT_REMEMBER_REFRESH_TOKEN_LIFETIME', timedelta(days=30))
        else:
            # Standard lifetimes from settings
            access_lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=60))
            refresh_lifetime = settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timedelta(days=7))
        
        # Create a new refresh token with custom lifetime
        refresh.set_exp(lifetime=refresh_lifetime)
        
        # Create access token with custom lifetime
        access_token = refresh.access_token
        access_token.set_exp(lifetime=access_lifetime)
        
        # Update the response data with new tokens
        data['refresh'] = str(refresh)
        data['access'] = str(access_token)
        
        # Add remember_me flag to response for client-side use
        data['remember_me'] = remember_me
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view that handles remember_me parameter
    to provide different token expiration times.
    
    This view replaces the default Djoser TokenObtainPairView to support
    dynamic token lifetimes based on user preference.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Override post method to handle custom logic if needed.
        """
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            # Log successful authentication with remember_me status
            remember_me = request.data.get('remember_me', False)
            user = self.get_serializer().user if hasattr(self.get_serializer(), 'user') else None
            
            # You can add logging here if needed
            # logger.info(f"User {user.username if user else 'unknown'} logged in with remember_me={remember_me}")
        
        return response
