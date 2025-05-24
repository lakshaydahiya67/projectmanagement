from django.urls import path, include
from rest_framework_nested import routers
from rest_framework import routers as drf_routers
from .views import LabelViewSet, TaskViewSet, CommentViewSet, AttachmentViewSet

# Direct route for tasks - enables direct access to /api/v1/tasks/
task_direct_router = drf_routers.DefaultRouter()
task_direct_router.register(r'', TaskViewSet, basename='task')  # Empty string to avoid double 'tasks'

# Project labels
project_router = routers.SimpleRouter()
project_router.register(r'projects/(?P<project_pk>[^/.]+)/labels', LabelViewSet, basename='project-labels')

urlpatterns = [
    # Direct access to tasks - this enables POST /api/v1/tasks/
    path('', include(task_direct_router.urls)),
    path('', include(project_router.urls)),
]
