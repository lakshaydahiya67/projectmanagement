from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
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
