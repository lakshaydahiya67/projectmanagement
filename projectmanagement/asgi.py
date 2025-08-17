"""
ASGI config for projectmanagement project.

Simple ASGI configuration without WebSocket support.
For production, consider using WSGI instead.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')

application = get_asgi_application()