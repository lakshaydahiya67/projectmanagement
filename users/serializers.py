from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from djoser.serializers import UserCreatePasswordRetypeSerializer as BaseUserCreateSerializer
from .models import UserPreference
import re
import logging
import sys

# Set up logging for debugging
logger = logging.getLogger('users.serializers')

User = get_user_model()

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['theme_preference', 'email_notifications', 'push_notifications']

class UserSerializer(serializers.ModelSerializer):
    preferences = UserPreferenceSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'profile_picture', 'phone_number', 'job_title', 'bio', 
                  'date_joined', 'last_modified', 'preferences']
        read_only_fields = ['date_joined', 'last_modified']
        ref_name = 'ProjectUser'  # Unique reference name for Swagger

class UserDetailSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['is_active', 'last_login']

class UserCreateSerializer(BaseUserCreateSerializer):
    # No need to declare password and re_password again - they're inherited from BaseUserCreateSerializer
    
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = BaseUserCreateSerializer.Meta.fields + (
            'first_name', 'last_name', 'profile_picture', 'phone_number', 
            'job_title', 'bio'
        )
    
    def __init__(self, *args, **kwargs):
        print(f"DEBUG: UserCreateSerializer.__init__() called", flush=True)
        sys.stdout.flush()
        logger.critical(f"UserCreateSerializer.__init__() called")
        super().__init__(*args, **kwargs)
        print(f"DEBUG: UserCreateSerializer fields: {list(self.fields.keys())}", flush=True)
        sys.stdout.flush()
        logger.critical(f"UserCreateSerializer fields: {list(self.fields.keys())}")
    
    def validate_email(self, value):
        """Validate email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_password(self, value):
        """Validate password complexity"""
        print(f"DEBUG: UserCreateSerializer.validate_password() called with: {value}", flush=True)
        sys.stdout.flush()
        logger.critical(f"UserCreateSerializer.validate_password() called with: {value}")
        try:
            # Use Django's built-in password validation
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
            
        # Additional custom validation
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
            
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
            
        if not any(char.islower() for char in value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
            
        if not any(char in "!@#$%^&*()_-+={}[]\\|:;\"'<>,.?/" for char in value):
            raise serializers.ValidationError("Password must contain at least one special character.")
            
        return value
    
    def validate(self, attrs):
        print(f"DEBUG: UserCreateSerializer.validate() called with attrs: {attrs}", flush=True)
        sys.stdout.flush()
        logger.critical(f"UserCreateSerializer.validate() called with attrs: {attrs}")
        # Let the parent class handle password validation
        attrs = super().validate(attrs)
        print(f"DEBUG: After parent validation, attrs: {attrs}", flush=True)
        sys.stdout.flush()
        logger.critical(f"After parent validation, attrs: {attrs}")
        return attrs
    
    def create(self, validated_data):
        print(f"DEBUG: UserCreateSerializer.create() called with validated_data: {validated_data}", flush=True)
        sys.stdout.flush()
        logger.critical(f"UserCreateSerializer.create() called with validated_data: {validated_data}")
        # Let the parent Djoser serializer handle the creation
        user = super().create(validated_data)
        print(f"DEBUG: User created: {user.username}, first_name: '{user.first_name}', last_name: '{user.last_name}'", flush=True)
        sys.stdout.flush()
        logger.critical(f"User created: {user.username}, first_name: '{user.first_name}', last_name: '{user.last_name}'")
        
        # UserPreference will be created via signal handler
        
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    first_name = serializers.CharField(required=True, max_length=150, allow_blank=False)
    last_name = serializers.CharField(required=True, max_length=150, allow_blank=False)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'profile_picture', 'phone_number', 
                  'job_title', 'bio']
    
    def validate_first_name(self, value):
        """Ensure first name is not empty or just whitespace"""
        if not value or not value.strip():
            raise serializers.ValidationError("First name cannot be empty.")
        return value.strip()
    
    def validate_last_name(self, value):
        """Ensure last name is not empty or just whitespace"""
        if not value or not value.strip():
            raise serializers.ValidationError("Last name cannot be empty.")
        return value.strip()
    
    def update(self, instance, validated_data):
        # Handle profile picture update separately
        profile_picture = validated_data.pop('profile_picture', None)
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Only update profile_picture if it was provided in the request
        if profile_picture is not None:
            instance.profile_picture = profile_picture
            
        instance.save()
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate_new_password(self, value):
        """Validate password complexity"""
        try:
            # Use Django's built-in password validation
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
            
        # Additional custom validation
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
            
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
            
        if not any(char.islower() for char in value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
            
        if not any(char in "!@#$%^&*()_-+={}[]\\|:;\"'<>,.?/" for char in value):
            raise serializers.ValidationError("Password must contain at least one special character.")
            
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password fields didn't match."})
        return attrs
