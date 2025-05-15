from django.urls import path, include
from rest_framework_nested import routers
from .views import ActivityLogViewSet, ProjectMetricViewSet, UserProductivityViewSet, RecentBoardsView, UpcomingTasksView

# Activity logs for organizations
org_router = routers.SimpleRouter()
org_router.register(r'organizations/(?P<organization_pk>[^/.]+)/activities', ActivityLogViewSet, basename='organization-activities')

# Metrics for projects
project_router = routers.SimpleRouter()
project_router.register(r'projects/(?P<project_pk>[^/.]+)/metrics', ProjectMetricViewSet, basename='project-metrics')
project_router.register(r'projects/(?P<project_pk>[^/.]+)/productivity', UserProductivityViewSet, basename='user-productivity')

urlpatterns = [
    path('', include(org_router.urls)),
    path('', include(project_router.urls)),
    # Add routes for recent boards and upcoming tasks
    path('boards/recent/', RecentBoardsView.as_view(), name='recent-boards'),
    path('tasks/upcoming/', UpcomingTasksView.as_view(), name='upcoming-tasks'),
]
