from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import OrganizationViewSet, OrganizationMemberViewSet, OrganizationInvitationViewSet, OrganizationProjectsView

router = DefaultRouter()
router.register(r'', OrganizationViewSet)

# Nested routes for organization members and invitations
organizations_router = routers.NestedSimpleRouter(router, r'', lookup='organization')
organizations_router.register(r'members', OrganizationMemberViewSet, basename='organization-members')
organizations_router.register(r'invitations', OrganizationInvitationViewSet, basename='organization-invitations')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(organizations_router.urls)),
    path('<uuid:organization_id>/projects/', OrganizationProjectsView.as_view(), name='organization-projects'),
]
