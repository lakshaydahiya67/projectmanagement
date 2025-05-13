from django.urls import path
from projects.consumers import ProjectConsumer, BoardConsumer
from notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path('ws/projects/<str:project_id>/', ProjectConsumer.as_asgi()),
    path('ws/boards/<str:board_id>/', BoardConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]
