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
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def health_check(request):
    """Health check endpoint for Docker"""
    return JsonResponse({"status": "ok"})

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
    
    # Health check for Docker
    path('api/v1/health/', health_check, name='health_check'),
    
    # Include app URLs
    path('api/v1/', include(api_patterns)),
    
    # API Documentation
    re_path(r'^api/docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^api/redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
