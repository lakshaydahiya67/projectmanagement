from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .models import UserPreference
from .serializers import (
    UserSerializer, UserDetailSerializer, UserCreateSerializer, 
    UserUpdateSerializer, UserPreferenceSerializer, ChangePasswordSerializer
)
from .permissions import IsUserOrReadOnly, IsUserOwner

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Admin can see all users, regular users only see themselves
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsUserOwner])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.validated_data.get('old_password')):
                return Response({"old_password": ["Wrong password."]}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # set_password hashes the password
            user.set_password(serializer.validated_data.get('new_password'))
            user.save()
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
