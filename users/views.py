from rest_framework import viewsets, generics, status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from .permissions import AllowPasswordReset
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .models import UserPreference
from .serializers import (
    UserSerializer, UserDetailSerializer, UserCreateSerializer, 
    UserUpdateSerializer, UserPreferenceSerializer, ChangePasswordSerializer
)
from .permissions import IsUserOrReadOnly, IsUserOwner
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .email import PasswordResetEmail, ActivationEmail, send_password_reset_email
import logging

# Try to import ActivityLog model if available
try:
    from activitylogs.models import ActivityLog
    ACTIVITY_LOGS_ENABLED = True
except ImportError:
    ACTIVITY_LOGS_ENABLED = False

User = get_user_model()

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Admin can see all users, regular users only see themselves and users from their organizations
        user = self.request.user
        
        # Check if this is a schema generation request for Swagger
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
            
        if user.is_staff or user.is_superuser:
            return User.objects.all()
            
        # Get organizations the user is a member of
        try:
            from organizations.models import OrganizationMember
            user_orgs = OrganizationMember.objects.filter(user=user).values_list('organization_id', flat=True)
            org_users = OrganizationMember.objects.filter(organization_id__in=user_orgs).values_list('user_id', flat=True)
            return User.objects.filter(id__in=list(org_users))
        except ImportError:
            # Organizations app not available, just return the current user
            return User.objects.filter(id=user.id)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsUserOwner]
        elif self.action == 'create':
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()
    
    @transaction.atomic
    def perform_update(self, serializer):
        """Override perform_update to add activity logging"""
        instance = serializer.save()
        
        # Log the update if activity logs are enabled
        if ACTIVITY_LOGS_ENABLED:
            ActivityLog.objects.create(
                user=self.request.user,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=str(instance.id),
                action_type=ActivityLog.UPDATED,
                description=f"User profile updated"
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsUserOwner])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.validated_data.get('old_password')):
                return Response({"old_password": ["Wrong password."]}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # set_password hashes the password
                user.set_password(serializer.validated_data.get('new_password'))
                user.save()
                
                # Log the password change if activity logs are enabled
                if ACTIVITY_LOGS_ENABLED:
                    ActivityLog.objects.create(
                        user=request.user,
                        content_type=ContentType.objects.get_for_model(user),
                        object_id=str(user.id),
                        action_type=ActivityLog.UPDATED,
                        description="Password changed"
                    )
                    
            return Response({"status": "password changed successfully"}, 
                           status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        user = request.user
        
        if request.method == 'GET':
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            # Use UserUpdateSerializer for updates
            serializer = UserUpdateSerializer(user, data=request.data, partial=request.method == 'PATCH')
            
            if serializer.is_valid():
                with transaction.atomic():
                    # Save the user instance
                    serializer.save()
                    
                    # Log the update if activity logs are enabled
                    if ACTIVITY_LOGS_ENABLED:
                        ActivityLog.objects.create(
                            user=request.user,
                            content_type=ContentType.objects.get_for_model(user),
                            object_id=str(user.id),
                            action_type=ActivityLog.UPDATED,
                            description="User profile updated"
                        )
                
                return Response(UserDetailSerializer(user).data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserPreferenceView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to get and update user preferences
    """
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Get or create preferences for the user
        preferences, created = UserPreference.objects.get_or_create(user=self.request.user)
        return preferences
    
    @transaction.atomic
    def perform_update(self, serializer):
        """Override perform_update to add activity logging"""
        instance = serializer.save()
        
        # Log the update if activity logs are enabled
        if ACTIVITY_LOGS_ENABLED:
            ActivityLog.objects.create(
                user=self.request.user,
                content_type=ContentType.objects.get_for_model(self.request.user),
                object_id=str(self.request.user.id),
                action_type=ActivityLog.UPDATED,
                description="User preferences updated"
            )

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def custom_password_reset(request):
    """
    Custom password reset view that directly uses our email sending logic.
    This overrides Djoser's default password reset view.
    """
    # Log the request for debugging
    logger.info(f"Password reset request received for: {request.data.get('email', 'unknown')}"
               f" from {request.META.get('REMOTE_ADDR')}"
               f" with auth: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
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


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def test_reset_email(request):
    """
    Test endpoint to verify password reset email functionality.
    This is for development/testing only and should be disabled in production.
    """
    if not settings.DEBUG:
        return Response({"detail": "This endpoint is only available in DEBUG mode."}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    email = request.data.get('email', '')
    if not email:
        return Response({"detail": "Email is required."}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Create a minimal user object for testing
    class TestUser:
        def __init__(self, email):
            self.email = email
            self.username = email
            self.pk = 1
            
        def get_full_name(self):
            return self.username
            
    user = TestUser(email)
    
    try:
        # Create a password reset email using your custom email class
        email_instance = PasswordResetEmail({'user': user, 'protocol': 'http'})
        context = email_instance.get_context_data()
        
        # Send email using standard Django send_mail
        result = send_mail(
            subject="Test Password Reset Email",
            message=f"This is a test password reset email. Please use this link: {context.get('reset_url')}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
            html_message=f"<h1>Test Password Reset</h1><p>This is a test email to verify the email system.</p><p>Reset URL: <a href='{context.get('reset_url')}'>{context.get('reset_url')}</a></p>"
        )
        
        if result:
            logger.info(f"Test password reset email sent successfully to {email}")
            return Response({
                "detail": "Test password reset email sent successfully.",
                "reset_url": context.get('reset_url'),
                "debug_info": context
            })
        else:
            logger.error(f"Failed to send test password reset email to {email}")
            return Response({
                "detail": "Failed to send test email. Check server logs for details.",
                "debug_info": context
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.exception(f"Error sending test password reset email: {str(e)}")
        return Response({
            "detail": f"Error: {str(e)}",
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
