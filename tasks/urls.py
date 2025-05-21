from django.urls import path, include
from rest_framework_nested import routers
from rest_framework import routers as drf_routers
from .views import LabelViewSet, TaskViewSet, CommentViewSet, AttachmentViewSet

# Direct route for tasks
task_direct_router = drf_routers.DefaultRouter()
task_direct_router.register(r'tasks', TaskViewSet, basename='task')

# Tasks are nested under columns
column_router = routers.SimpleRouter()
column_router.register(r'columns', TaskViewSet, basename='column-tasks')

# Nested routes for task resources
tasks_router = routers.NestedSimpleRouter(column_router, r'columns', lookup='column')
tasks_router.register(r'tasks', TaskViewSet, basename='tasks')

# Nested routes for task comments and attachments
task_resources_router = routers.NestedSimpleRouter(tasks_router, r'tasks', lookup='task')
task_resources_router.register(r'comments', CommentViewSet, basename='task-comments')
task_resources_router.register(r'attachments', AttachmentViewSet, basename='task-attachments')

# Project labels
project_router = routers.SimpleRouter()
project_router.register(r'projects/(?P<project_pk>[^/.]+)/labels', LabelViewSet, basename='project-labels')

urlpatterns = [
    # Direct access to tasks
    path('', include(task_direct_router.urls)),
    # Nested routes
    path('', include(column_router.urls)),
    path('', include(tasks_router.urls)),
    path('', include(task_resources_router.urls)),
    path('', include(project_router.urls)),
]
