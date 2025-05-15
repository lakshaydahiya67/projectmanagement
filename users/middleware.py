from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_key):
    """
    Get the user from the JWT token.
    """
    try:
        # Validate the token
        token = AccessToken(token_key)
        user_id = token.payload.get('user_id')
        
        # If no user ID in token, return AnonymousUser
        if not user_id:
            return AnonymousUser()
            
        # Get the user
        user = User.objects.get(id=user_id)
        return user
    except (InvalidToken, TokenError, User.DoesNotExist):
        # If token is invalid or user doesn't exist, return AnonymousUser
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware that authenticates WebSocket connections using JWT tokens.
    """
    async def __call__(self, scope, receive, send):
        # Try to get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [''])[0]
        
        # If no token in query string, try to get from headers
        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Get user from token
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send) 