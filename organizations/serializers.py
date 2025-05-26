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
    role = serializers.ChoiceField(
        choices=OrganizationMember.ROLE_CHOICES,
        required=True,
        help_text="User's role in the organization (admin, manager, or member)"
    )
    
    class Meta:
        model = OrganizationMember
        fields = ['role']
        
    def validate_role(self, value):
        # Ensure the role is valid
        valid_roles = [role[0] for role in OrganizationMember.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        return value

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
        read_only_fields = ['created_at', 'expires_at', 'accepted', 'invited_by', 'organization']
        extra_kwargs = {
            'token': {'write_only': True, 'required': False}
        }
    
    def create(self, validated_data):
        """
        Override create method to ensure token is properly generated
        """
        # Token will be generated automatically in the model's save method
        invitation = OrganizationInvitation(**validated_data)
        invitation.save()
        return invitation
