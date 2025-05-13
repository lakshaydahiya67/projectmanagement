from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserPreferenceView

router = DefaultRouter()
router.register(r'', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('me/preferences/', UserPreferenceView.as_view(), name='user-preferences'),
]
