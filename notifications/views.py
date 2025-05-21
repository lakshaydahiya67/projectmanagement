from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Notification, NotificationSetting
from .serializers import NotificationSerializer, NotificationSettingSerializer

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['read', 'notification_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Check if this is a schema generation request for Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
            
        # Only show notifications for the current user
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        
        if not notification.read:
            notification.read = True
            notification.read_at = timezone.now()
            notification.save()
            
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            read=False
        )
        
        now = timezone.now()
        for notification in unread_notifications:
            notification.read = True
            notification.read_at = now
            notification.save()
            
        return Response({"status": "All notifications marked as read"})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            recipient=request.user,
            read=False
        ).count()
        
        return Response({"unread_count": count})

class NotificationSettingView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to get and update notification settings
    """
    serializer_class = NotificationSettingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Get or create notification settings for the user
        settings, created = NotificationSetting.objects.get_or_create(user=self.request.user)
        return settings
