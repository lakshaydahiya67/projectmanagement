from django.urls import path, include
from rest_framework_nested import routers
from .views import LabelViewSet, TaskViewSet, CommentViewSet, AttachmentViewSet

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
    path('', include(column_router.urls)),
    path('', include(tasks_router.urls)),
    path('', include(task_resources_router.urls)),
    path('', include(project_router.urls)),
]
