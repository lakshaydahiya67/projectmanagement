from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import ProjectViewSet, ProjectMemberViewSet, BoardViewSet, ColumnViewSet

router = DefaultRouter()
router.register(r'', ProjectViewSet)

# Nested routes for project members
projects_router = routers.NestedSimpleRouter(router, r'', lookup='project')
projects_router.register(r'members', ProjectMemberViewSet, basename='project-members')
projects_router.register(r'boards', BoardViewSet, basename='project-boards')

# Nested routes for board columns
boards_router = routers.NestedSimpleRouter(projects_router, r'boards', lookup='board')
boards_router.register(r'columns', ColumnViewSet, basename='board-columns')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
    path('', include(boards_router.urls)),
]
