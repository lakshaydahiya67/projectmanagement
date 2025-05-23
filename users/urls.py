from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserPreferenceView, test_reset_email, custom_password_reset
from .test_email import test_password_reset_email, test_direct_email
from .public_views import public_password_reset

router = DefaultRouter()
router.register(r'', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('preferences/', UserPreferenceView.as_view(), name='user-preferences'),
    path('password-reset/', public_password_reset, name='public-password-reset'),  # Use the public view instead
    path('test-reset-email/', test_reset_email, name='test-reset-email'),
    path('test/password-reset-email/', test_password_reset_email, name='test-password-reset-email'),
    path('test/direct-email/', test_direct_email, name='test-direct-email'),
]
