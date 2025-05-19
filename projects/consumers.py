import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from projects.models import Project, ProjectMember, Board
from projects.models import BoardViewer

class ProjectConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for project-level events"""
    
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.project_group_name = f'project_{self.project_id}'
        
        # Check if user has access to this project
        if not await self.user_has_project_access():
            await self.close(code=4003)  # 4003 = Authentication failed
            return
        
        # Join the project group
        await self.channel_layer.group_add(
            self.project_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Add user to active viewers
        user_data = await self.get_user_data()
        await self.channel_layer.group_send(
            self.project_group_name,
            {
                'type': 'user_joined',
                'user': user_data
            }
        )
    
    async def disconnect(self, close_code):
        # Leave the project group
        if hasattr(self, 'project_group_name'):
            # Notify others that user has left
            user_data = await self.get_user_data()
            await self.channel_layer.group_send(
                self.project_group_name,
                {
                    'type': 'user_left',
                    'user': user_data
                }
            )
            
            await self.channel_layer.group_discard(
                self.project_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        Parse the message and perform actions based on the message type.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'task_update':
                await self.channel_layer.group_send(
                    self.project_group_name,
                    {
                        'type': 'task_update_message',
                        'task_id': data.get('task_id'),
                        'updates': data.get('updates'),
                        'user': await self.get_user_data()
                    }
                )
            elif message_type == 'comment_add':
                await self.channel_layer.group_send(
                    self.project_group_name,
                    {
                        'type': 'comment_add_message',
                        'task_id': data.get('task_id'),
                        'comment': data.get('comment'),
                        'user': await self.get_user_data()
                    }
                )
            elif message_type == 'heartbeat':
                # Just acknowledge heartbeat
                pass
        except json.JSONDecodeError:
            pass
    
    async def task_update_message(self, event):
        """Send task update message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'task_update',
            'task_id': event['task_id'],
            'updates': event['updates'],
            'user': event['user']
        }))
    
    async def comment_add_message(self, event):
        """Send comment add message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'comment_add',
            'task_id': event['task_id'],
            'comment': event['comment'],
            'user': event['user']
        }))
    
    async def user_joined(self, event):
        """Send user joined message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user']
        }))
    
    async def user_left(self, event):
        """Send user left message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user']
        }))
    
    async def notification_message(self, event):
        """Send notification message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    @database_sync_to_async
    def user_has_project_access(self):
        """Check if the user has access to this project"""
        user = self.scope['user']
        if not user.is_authenticated:
            return False
            
        try:
            project = Project.objects.get(id=self.project_id)
            
            # Check if user is a member of this project
            is_member = ProjectMember.objects.filter(
                project=project,
                user=user
            ).exists()
            
            # If not a member, check if project is public and user is in the organization
            if not is_member and project.is_public:
                return project.organization.members.filter(user=user).exists()
            
            return is_member
        except Project.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_user_data(self):
        """Get user data to send in messages"""
        user = self.scope['user']
        return {
            'id': str(user.id),  # Convert UUID to string
            'username': user.username,
            'full_name': user.get_full_name(),
            'avatar': user.get_profile_picture_url() if hasattr(user, 'get_profile_picture_url') else (user.profile_picture.url if user.profile_picture else None)
        }


class BoardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for board-level events (more focused on kanban board)"""
    
    async def connect(self):
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        self.board_group_name = f'board_{self.board_id}'
        
        # Check if user has access to this board
        if not await self.user_has_board_access():
            await self.close(code=4003)  # 4003 = Authentication failed
            return
        
        # Join the board group
        await self.channel_layer.group_add(
            self.board_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Add user to board_viewers in database
        await self.add_user_to_viewers()
        
        # Add user to active viewers
        user_data = await self.get_user_data()
        
        # Get all current viewers
        current_viewers = await self.get_current_viewers()
        
        # First send the current viewers to the new user
        await self.send(text_data=json.dumps({
            'type': 'current_viewers',
            'viewers': current_viewers
        }))
        
        # Then notify everyone that a new user joined
        await self.channel_layer.group_send(
            self.board_group_name,
            {
                'type': 'user_joined',
                'user': user_data
            }
        )
    
    async def disconnect(self, close_code):
        # Leave the board group
        if hasattr(self, 'board_group_name'):
            # Remove user from board viewers in database
            await self.remove_user_from_viewers()
            
            # Notify others that user has left
            user_data = await self.get_user_data()
            await self.channel_layer.group_send(
                self.board_group_name,
                {
                    'type': 'user_left',
                    'user': user_data
                }
            )
            
            await self.channel_layer.group_discard(
                self.board_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'heartbeat':
                # Update user's last activity time
                await self.add_user_to_viewers()
                
                # Send back updated viewer list to all clients
                current_viewers = await self.get_current_viewers()
                await self.channel_layer.group_send(
                    self.board_group_name,
                    {
                        'type': 'current_viewers_message',
                        'viewers': current_viewers
                    }
                )
        except json.JSONDecodeError:
            pass
    
    async def task_move_message(self, event):
        """Send task move message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'task_move',
            'task_id': event['task_id'],
            'source_column_id': event['source_column_id'],
            'destination_column_id': event['destination_column_id'],
            'order': event['order'],
            'user': event['user']
        }))
    
    async def task_create_message(self, event):
        """Send task creation message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'task_create',
            'task': event['task'],
            'column_id': event['column_id'],
            'user': event['user']
        }))
    
    async def task_label_message(self, event):
        """Send task label update message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'task_label_update',
            'task_id': event['task_id'],
            'labels': event['labels'],
            'user': event['user']
        }))
    
    async def column_update_message(self, event):
        """Send column update message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'column_update',
            'column_id': event['column_id'],
            'updates': event['updates'],
            'user': event['user']
        }))
    
    async def current_viewers_message(self, event):
        """Send the list of current viewers to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'current_viewers',
            'viewers': event['viewers']
        }))
    
    async def user_joined(self, event):
        """Send user joined message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user']
        }))
    
    async def user_left(self, event):
        """Send user left message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user']
        }))
    
    @database_sync_to_async
    def user_has_board_access(self):
        """Check if the user has access to this board"""
        user = self.scope['user']
        if not user.is_authenticated:
            return False
            
        try:
            board = Board.objects.select_related('project').get(id=self.board_id)
            project = board.project
            
            # Check if user is a member of this project
            is_member = ProjectMember.objects.filter(
                project=project,
                user=user
            ).exists()
            
            # If not a member, check if project is public and user is in the organization
            if not is_member and project.is_public:
                return project.organization.members.filter(user=user).exists()
            
            return is_member
        except Board.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_user_data(self):
        """Get user data to send in messages"""
        user = self.scope['user']
        return {
            'id': str(user.id),  # Convert UUID to string
            'username': user.username,
            'full_name': user.get_full_name(),
            'avatar': user.get_profile_picture_url() if hasattr(user, 'get_profile_picture_url') else (user.profile_picture.url if user.profile_picture else None)
        }
    
    @database_sync_to_async
    def add_user_to_viewers(self):
        """Add the current user to the board viewers"""
        user = self.scope['user']
        BoardViewer.add_or_update_viewer(self.board_id, user.id)
    
    @database_sync_to_async
    def remove_user_from_viewers(self):
        """Remove the current user from the board viewers"""
        user = self.scope['user']
        BoardViewer.remove_viewer(self.board_id, user.id)
    
    @database_sync_to_async
    def get_current_viewers(self):
        """Get current viewers of the board"""
        viewers = BoardViewer.get_active_viewers(self.board_id)
        
        # Format viewer data for the frontend
        return [
            {
                'id': str(viewer.user.id),  # Convert UUID to string
                'username': viewer.user.username,
                'full_name': viewer.user.get_full_name(),
                'avatar': viewer.user.get_profile_picture_url() if hasattr(viewer.user, 'get_profile_picture_url') else (viewer.user.profile_picture.url if viewer.user.profile_picture else None),
                'joined_at': viewer.joined_at.isoformat()
            } for viewer in viewers
        ]
