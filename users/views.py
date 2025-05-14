from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from .models import UserPreference
from .serializers import (
    UserSerializer, UserDetailSerializer, UserCreateSerializer, 
    UserUpdateSerializer, UserPreferenceSerializer, ChangePasswordSerializer
)
from .permissions import IsUserOrReadOnly, IsUserOwner

# Try to import ActivityLog model if available
try:
    from activitylogs.models import ActivityLog
    ACTIVITY_LOGS_ENABLED = True
except ImportError:
    ACTIVITY_LOGS_ENABLED = False

User = get_user_model()

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
                action=ActivityLog.UPDATE,
                details=f"User profile updated"
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
                        action=ActivityLog.UPDATE,
                        details="Password changed"
                    )
                    
            return Response({"status": "password changed successfully"}, 
                           status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

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
                action=ActivityLog.UPDATE,
                details="User preferences updated"
            )
