"""
URL patterns for public endpoints that bypass authentication.
These endpoints are designed to be accessible without any authentication.
"""

from django.urls import path
from .public_views import public_password_reset

# These URL patterns are included directly in the main urls.py
# They are not nested under /api/v1/ to avoid authentication middleware
urlpatterns = [
    path('', public_password_reset, name='public-password-reset'),
]
