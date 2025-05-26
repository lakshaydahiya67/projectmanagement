from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import ProjectViewSet, ProjectMemberViewSet, BoardViewSet, ColumnViewSet

# Import TaskViewSet from tasks app for nested routing
from tasks.views import TaskViewSet
# Import ActivityLogViewSet from analytics app for project activity logs
from analytics.views import ActivityLogViewSet

router = DefaultRouter()
router.register(r'', ProjectViewSet)

# Nested routes for project members
projects_router = routers.NestedSimpleRouter(router, r'', lookup='project')
projects_router.register(r'members', ProjectMemberViewSet, basename='project-members')
projects_router.register(r'boards', BoardViewSet, basename='project-boards')
projects_router.register(r'tasks', TaskViewSet, basename='project-tasks')  # Direct tasks route for project tasks
projects_router.register(r'activity_logs', ActivityLogViewSet, basename='project-activity-logs')  # Activity logs for projects

# Nested routes for board columns
boards_router = routers.NestedSimpleRouter(projects_router, r'boards', lookup='board')
boards_router.register(r'columns', ColumnViewSet, basename='board-columns')

# Nested routes for column tasks
columns_router = routers.NestedSimpleRouter(boards_router, r'columns', lookup='column')
columns_router.register(r'tasks', TaskViewSet, basename='column-tasks')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
    path('', include(boards_router.urls)),
    path('', include(columns_router.urls)),
]
