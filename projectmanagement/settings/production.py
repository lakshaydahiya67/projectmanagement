"""
Production settings for projectmanagement project, used on Render.com.
"""
import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Replace 'from ..settings import *' with a more explicit import mechanism
from .. import settings as base_settings_module
for attr_name in dir(base_settings_module):
    if not attr_name.startswith('_'):  # Import all names not starting with an underscore
        globals()[attr_name] = getattr(base_settings_module, attr_name)

# Explicitly define INSTALLED_APPS to ensure all required apps are included
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'channels',
    'django_filters',
    'drf_yasg',
    # Local apps
    'users',
    'organizations',
    'projects',
    'tasks',
    'notifications',
    'analytics',
    'activitylogs',
]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# CORS settings
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'https://projectmanagement-frontend.onrender.com,http://localhost:3000').split(',')

# CSRF and cookie settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# HTTPS settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database - use Render PostgreSQL
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Redis cache and Celery settings
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
