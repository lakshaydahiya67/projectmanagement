from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q
from django.utils import timezone
from django.db.models import Q
import uuid
import datetime

from .models import Organization, OrganizationMember, OrganizationInvitation
from .serializers import (
    OrganizationSerializer, OrganizationDetailSerializer,
    OrganizationMemberSerializer, OrganizationMemberUpdateSerializer,
    OrganizationInvitationSerializer
)
from .permissions import (
    IsOrganizationAdmin, IsOrganizationMember, 
    IsOrganizationAdminOrReadOnly
)

class OrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for organizations
    """
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Organization.objects.all()  # Add this line to fix the router issue
    
    def get_queryset(self):
        # Check if this is a schema generation request for Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Organization.objects.none()
            
        # Return organizations the user is a member of
        return Organization.objects.filter(
            members__user=self.request.user
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrganizationDetailSerializer
        return OrganizationSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        # Create organization and add current user as admin
        organization = serializer.save()
        OrganizationMember.objects.create(
            user=self.request.user,
            organization=organization,
            role=OrganizationMember.ADMIN
        )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all members of an organization"""
        organization = self.get_object()
        members = OrganizationMember.objects.filter(organization=organization)
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOrganizationAdmin])
    def invite(self, request, pk=None):
        """Invite a user to an organization"""
        organization = self.get_object()
        
        # Check if email and role are provided
        email = request.data.get('email')
        role = request.data.get('role', OrganizationMember.MEMBER)
        
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is already a member
        if OrganizationMember.objects.filter(
            organization=organization,
            user__email=email
        ).exists():
            return Response(
                {"detail": "User is already a member of this organization."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if invitation already exists and not expired
        existing_invitation = OrganizationInvitation.objects.filter(
            organization=organization,
            email=email,
            accepted=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if existing_invitation:
            serializer = OrganizationInvitationSerializer(existing_invitation)
            return Response(serializer.data)
        
        # Create invitation - let the model's save method handle token generation
        invitation = OrganizationInvitation(
            organization=organization,
            email=email,
            role=role,
            invited_by=request.user,
        )
        invitation.save()  # This will generate the token and set expires_at
        
        # TODO: Send email invitation
        
        serializer = OrganizationInvitationSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrganizationMemberViewSet(viewsets.ModelViewSet):
    """
    API endpoint for organization members
    """
    serializer_class = OrganizationMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]
    
    def get_queryset(self):
        organization_id = self.kwargs.get('organization_pk')
        return OrganizationMember.objects.filter(organization_id=organization_id)
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return OrganizationMemberUpdateSerializer
        return OrganizationMemberSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]
        return super().get_permissions()

class OrganizationInvitationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for organization invitations
    """
    serializer_class = OrganizationInvitationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]
    
    def get_queryset(self):
        organization_id = self.kwargs.get('organization_pk')
        return OrganizationInvitation.objects.filter(organization_id=organization_id)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None, organization_pk=None):
        """Accept an invitation to join an organization"""
        invitation = self.get_object()
        
        # Check if invitation is valid
        if invitation.accepted:
            return Response(
                {"detail": "Invitation has already been accepted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.is_expired:
            return Response(
                {"detail": "Invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email matches the current user
        if invitation.email != request.user.email:
            return Response(
                {"detail": "This invitation is for a different email address."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create organization membership
        OrganizationMember.objects.create(
            user=request.user,
            organization=invitation.organization,
            role=invitation.role
        )
        
        # Mark invitation as accepted
        invitation.accepted = True
        invitation.save(update_fields=['accepted'])
        
        return Response({"detail": "Successfully joined the organization."})
        
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOrganizationAdmin])
    def resend(self, request, pk=None, organization_pk=None):
        """Resend an invitation"""
        invitation = self.get_object()
        
        # Check if invitation is valid
        if invitation.accepted:
            return Response(
                {"detail": "Invitation has already been accepted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extend expiration date
        invitation.expires_at = timezone.now() + datetime.timedelta(days=7)
        invitation.save(update_fields=['expires_at'])
        
        # TODO: Resend email invitation
        
        serializer = self.get_serializer(invitation)
        return Response(serializer.data)

# View for rendering the organization detail HTML page
def organization_detail_view(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)
    # Basic permission check: user must be a member of the organization to view its details
    # More granular checks can be added if needed (e.g. using IsOrganizationMember permission class)
    if not OrganizationMember.objects.filter(organization=organization, user=request.user).exists() and not request.user.is_staff:
        # Or redirect to an error page/dashboard with a message
        return render(request, 'base/error.html', {'message': 'You do not have permission to view this organization.'}, status=403)
    
    return render(request, 'organization/detail.html', {'organization': organization})


# View for updating an organization
def organization_update_view(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)
    
    # Permission check: only organization admins or staff can update the organization
    member = OrganizationMember.objects.filter(organization=organization, user=request.user).first()
    if (not member or not member.is_admin) and not request.user.is_staff:
        return render(request, 'base/error.html', {'message': 'You do not have permission to update this organization.'}, status=403)
    
    if request.method == 'POST':
        # Process the form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        website = request.POST.get('website')
        
        if name:  # Name is required
            organization.name = name
            organization.description = description
            organization.website = website
            organization.save()
            
            # Redirect to the organization detail page
            return redirect('organization_detail', org_id=organization.id)
    
    # Render the update form
    return render(request, 'organization/update.html', {'organization': organization})


# View for rendering the organization list HTML page
def organization_list_view(request):
    """
    View function for rendering the organization list page with organizations the user belongs to
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    # Get organizations the user is a member of
    user_organizations = Organization.objects.filter(
        members__user=request.user
    ).distinct()
    
    context = {
        'organizations': user_organizations
    }
    
    return render(request, 'organization/list.html', context)


# View for handling organization deletion
def organization_delete_view(request, org_id):
    """
    View function for handling organization deletion
    Requires POST method and checks if user has admin permissions
    """
    organization = get_object_or_404(Organization, id=org_id)
    
    # Check if user is an organization admin
    member = OrganizationMember.objects.filter(
        organization=organization,
        user=request.user,
        is_admin=True
    ).first()
    
    if not member and not request.user.is_staff:
        return render(request, 'base/error.html', {
            'message': 'You do not have permission to delete this organization.'
        }, status=403)
    
    # Only process deletion on POST request
    if request.method == 'POST':
        # Delete the organization
        organization.delete()
        
        # Redirect to the organizations list
        from django.contrib import messages
        messages.success(request, f'Organization "{organization.name}" has been successfully deleted.')
        return redirect('organizations')
    
    # Render confirmation page for GET requests
    return render(request, 'organization/delete.html', {'organization': organization})


# API endpoint for organization projects
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from projects.models import Project
from projects.serializers import ProjectSerializer

class OrganizationProjectsView(APIView):
    """
    API endpoint for retrieving projects belonging to an organization
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, organization_id):
        # Check if user is a member of the organization
        is_member = OrganizationMember.objects.filter(
            organization_id=organization_id,
            user=request.user
        ).exists()
        
        if not is_member and not request.user.is_staff:
            return Response({'detail': 'You do not have permission to view projects in this organization.'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        # Get all projects for the organization that the user has access to
        # Either projects the user is a member of, or public projects in the organization
        projects = Project.objects.filter(
            organization_id=organization_id
        ).filter(
            Q(members__user=request.user) | Q(is_public=True)
        ).distinct()
        
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)
