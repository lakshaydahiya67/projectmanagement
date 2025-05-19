import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for user notifications"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close(code=4003)  # 4003 = Authentication failed
            return
        
        self.notification_group_name = f'user_notifications_{self.user.id}'
        
        # Join the notification group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send the initial unread count
        await self.send_unread_count()
    
    async def disconnect(self, close_code):
        # Leave the notification group
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        Handle client requests like marking notifications as read.
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_as_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    success = await self.mark_notification_as_read(notification_id)
                    if success:
                        await self.send_unread_count()
                        await self.send(text_data=json.dumps({
                            'type': 'mark_as_read_success',
                            'notification_id': notification_id
                        }))
                    else:
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'message': 'Notification not found or already read'
                        }))
            elif action == 'mark_all_as_read':
                success = await self.mark_all_notifications_as_read()
                if success:
                    await self.send_unread_count()
                    await self.send(text_data=json.dumps({
                        'type': 'mark_all_as_read_success'
                    }))
            elif action == 'heartbeat':
                # Just acknowledge the heartbeat
                pass
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown action: {action}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def notification_message(self, event):
        """Send notification message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
        
        # Update unread count after sending a new notification
        await self.send_unread_count()
    
    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Mark a notification as read"""
        from django.utils import timezone
        from notifications.models import Notification
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            if not notification.read:
                notification.read = True
                notification.read_at = timezone.now()
                notification.save()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_as_read(self):
        """Mark all notifications as read"""
        from django.utils import timezone
        from notifications.models import Notification
        
        Notification.objects.filter(
            recipient=self.user,
            read=False
        ).update(read=True, read_at=timezone.now())
        
        return True
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get the count of unread notifications"""
        from notifications.models import Notification
        
        return Notification.objects.filter(
            recipient=self.user,
            read=False
        ).count()
    
    async def send_unread_count(self):
        """Send unread count to the client"""
        count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))
