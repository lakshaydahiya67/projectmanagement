"""
URL configuration for projectmanagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
import redis
import os

def health_check(request):
    """Health check endpoint for Docker that verifies database and Redis connections"""
    status = {"status": "ok", "services": {}}
    
    # Check database connection
    try:
        db_conn = connections['default']
        db_conn.cursor()
        status["services"]["database"] = "up"
    except OperationalError:
        status["services"]["database"] = "down"
        status["status"] = "degraded"
    
    # Check Redis connection if used
    try:
        redis_host = os.environ.get('REDIS_HOST', '127.0.0.1')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        r = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=2)
        r.ping()
        status["services"]["redis"] = "up"
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        status["services"]["redis"] = "down"
        status["status"] = "degraded"
    
    return JsonResponse(status)

# API Documentation with Swagger/OpenAPI
schema_view = get_schema_view(
   openapi.Info(
      title="Project Management API",
      default_version='v1',
      description="API for Project Management Application",
      terms_of_service="https://www.projectmanagement.com/terms/",
      contact=openapi.Contact(email="contact@projectmanagement.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# API URL patterns
api_patterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('users/', include('users.urls')),
    path('organizations/', include('organizations.urls')),
    path('projects/', include('projects.urls')),
    path('tasks/', include('tasks.urls')),
    path('notifications/', include('notifications.urls')),
    path('analytics/', include('analytics.urls')),
    path('activity-logs/', include('activitylogs.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check for Docker and Render
    path('api/v1/health/', health_check, name='health_check'),
    path('api/health/', health_check, name='render_health_check'),
    
    # Frontend routes serving templates
    path('', TemplateView.as_view(template_name='dashboard/index.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='auth/login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard/dashboard.html'), name='dashboard'),
    path('projects/<uuid:project_id>/', TemplateView.as_view(template_name='dashboard/project_detail.html'), name='project_detail'),
    path('projects/<uuid:project_id>/boards/<uuid:board_id>/', TemplateView.as_view(template_name='board/board.html'), name='board_detail'),
    path('tasks/<uuid:task_id>/', TemplateView.as_view(template_name='task/task_detail.html'), name='task_detail'),
    path('organizations/', TemplateView.as_view(template_name='organization/list.html'), name='organizations'),
    path('organizations/<uuid:org_id>/', TemplateView.as_view(template_name='organization/detail.html'), name='organization_detail'),
    path('profile/', TemplateView.as_view(template_name='auth/profile.html'), name='profile'),
    
    # Include app URLs (API routes)
    path('api/v1/', include(api_patterns)),
    
    # API Documentation
    re_path(r'^api/docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^api/redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
