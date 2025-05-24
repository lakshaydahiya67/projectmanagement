"""
Custom JWT URLs that override Djoser's default JWT endpoints
to support remember_me functionality.
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from .jwt_views import CustomTokenObtainPairView

urlpatterns = [
    path('create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),
    path('refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    path('verify/', TokenVerifyView.as_view(), name='jwt-verify'),
    path('blacklist/', TokenBlacklistView.as_view(), name='jwt-blacklist'),
]
