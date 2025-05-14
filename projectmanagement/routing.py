from django.urls import path
from channels.routing import URLRouter

from notifications.consumers import NotificationConsumer
from projects.consumers import BoardConsumer, ProjectConsumer

websocket_urlpatterns = [
    path('ws/notifications/', NotificationConsumer.as_asgi()),
    path('ws/projects/<uuid:project_id>/', ProjectConsumer.as_asgi()),
    path('ws/boards/<uuid:board_id>/', BoardConsumer.as_asgi()),
]
