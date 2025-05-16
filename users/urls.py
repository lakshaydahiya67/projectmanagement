from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserPreferenceView, test_reset_email

router = DefaultRouter()
router.register(r'', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('preferences/', UserPreferenceView.as_view(), name='user-preferences'),
    path('test-reset-email/', test_reset_email, name='test-reset-email'),
]
