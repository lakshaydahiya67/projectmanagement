"""
ASGI config for projectmanagement project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import django

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')

# Initialize Django - this must be done before importing any models
django.setup()

# Now we can safely import Django-related modules
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from users.middleware import JWTAuthMiddleware

# Function to lazy-load the websocket URL patterns
def get_websocket_urlpatterns():
    from projectmanagement.routing import websocket_urlpatterns
    return websocket_urlpatterns

# Get the Django ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(
                get_websocket_urlpatterns()
            )
        )
    ),
})
