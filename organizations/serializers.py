from rest_framework import serializers
from .models import Organization, OrganizationMember, OrganizationInvitation
from users.serializers import UserSerializer

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'description', 'logo', 'website', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class OrganizationDetailSerializer(OrganizationSerializer):
    members_count = serializers.SerializerMethodField()
    
    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + ['members_count']
    
    def get_members_count(self, obj):
        return obj.members.count()

class OrganizationMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = ['id', 'user', 'organization', 'role', 'role_display', 'joined_at']
        read_only_fields = ['joined_at']

class OrganizationMemberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMember
        fields = ['role']

class OrganizationInvitationSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = OrganizationInvitation
        fields = [
            'id', 'organization', 'organization_name', 'email', 'role', 'role_display', 
            'invited_by', 'invited_by_name', 'token', 'created_at', 
            'expires_at', 'accepted', 'is_expired'
        ]
        read_only_fields = ['token', 'created_at', 'expires_at', 'accepted', 'invited_by', 'organization']
        extra_kwargs = {
            'token': {'write_only': True}
        }
