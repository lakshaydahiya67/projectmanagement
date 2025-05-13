from django.urls import path, include
from rest_framework_nested import routers
from .views import ActivityLogViewSet, ProjectMetricViewSet, UserProductivityViewSet

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
]
