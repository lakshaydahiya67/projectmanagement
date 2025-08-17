from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserPreferenceView

router = DefaultRouter()
router.register(r'', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('preferences/', UserPreferenceView.as_view(), name='user-preferences'),
    
    # Django authentication views for session-based auth
    path('login/', LoginView.as_view(template_name='auth/login.html'), name='user_login'),
    path('logout/', LogoutView.as_view(), name='user_logout'),
    path('password-reset/', PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
]
