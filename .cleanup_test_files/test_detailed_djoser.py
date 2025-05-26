#!/usr/bin/env python3
"""
Advanced debugging for Djoser registration process
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.serializers import UserCreateSerializer
from djoser import utils
from djoser.conf import settings as djoser_settings
from django.db import transaction
import json

User = get_user_model()

def test_detailed_registration():
    """Test the complete Djoser registration process step by step"""
    
    print("=" * 70)
    print("DETAILED DJOSER REGISTRATION DEBUG")
    print("=" * 70)
    
    # Test data
    registration_data = {
        "username": "debug_user_detailed",
        "email": "debug_detailed@example.com", 
        "password": "TestPass123!",
        "re_password": "TestPass123!",
        "first_name": "DebugFirst",
        "last_name": "DebugLast"
    }
    
    print(f"\n1. Testing with registration data:")
    print(json.dumps(registration_data, indent=2))
    
    # Clean up any existing user first
    User.objects.filter(email=registration_data["email"]).delete()
    
    # Step 1: Test our serializer directly
    print(f"\n2. Testing UserCreateSerializer directly:")
    serializer = UserCreateSerializer(data=registration_data)
    
    if serializer.is_valid():
        print(f"✅ Serializer validation passed")
        print(f"Validated data: {serializer.validated_data}")
        
        # Create user through serializer
        with transaction.atomic():
            user = serializer.save()
            print(f"✅ User created via direct serializer:")
            print(f"   - ID: {user.id}")
            print(f"   - Username: {user.username}")
            print(f"   - Email: {user.email}")
            print(f"   - First name: '{user.first_name}'")
            print(f"   - Last name: '{user.last_name}'")
            print(f"   - Is active: {user.is_active}")
        
        # Clean up for next test
        user.delete()
        print(f"   - User deleted for next test")
    else:
        print(f"❌ Serializer validation failed: {serializer.errors}")
        return False
    
    # Step 2: Test via Djoser's registration view logic (simulate the view)
    print(f"\n3. Testing Djoser registration flow simulation:")
    
    # Check Djoser settings
    print(f"   - Djoser USER_CREATE_SERIALIZER: {djoser_settings.SERIALIZERS['user_create']}")
    print(f"   - SEND_ACTIVATION_EMAIL: {djoser_settings.SEND_ACTIVATION_EMAIL}")
    
    # Simulate what Djoser's CreateView does
    serializer = UserCreateSerializer(data=registration_data)
    
    if serializer.is_valid():
        print(f"✅ Djoser-style validation passed")
        
        # Perform the create operation with all Djoser hooks
        with transaction.atomic():
            user = serializer.save()
            
            print(f"✅ User created via Djoser simulation:")
            print(f"   - ID: {user.id}")
            print(f"   - Username: {user.username}")
            print(f"   - Email: {user.email}")
            print(f"   - First name: '{user.first_name}'")
            print(f"   - Last name: '{user.last_name}'")
            print(f"   - Is active: {user.is_active}")
            
            # Check if activation is needed
            if djoser_settings.SEND_ACTIVATION_EMAIL:
                if not user.is_active:
                    print(f"   - User requires activation (is_active=False)")
                else:
                    print(f"   - User is already active")
            
            # Test the database state
            db_user = User.objects.get(id=user.id)
            print(f"✅ Database verification:")
            print(f"   - DB First name: '{db_user.first_name}'")
            print(f"   - DB Last name: '{db_user.last_name}'")
            
            if db_user.first_name == registration_data["first_name"] and db_user.last_name == registration_data["last_name"]:
                print(f"✅ SUCCESS: Names are correctly stored in database!")
                return True
            else:
                print(f"❌ FAILURE: Names not stored correctly in database!")
                return False
    else:
        print(f"❌ Djoser-style validation failed: {serializer.errors}")
        return False

if __name__ == "__main__":
    success = test_detailed_registration()
    print(f"\n{'='*70}")
    if success:
        print("🎉 DETAILED DEBUG PASSED: Djoser registration works correctly!")
    else:
        print("❌ DETAILED DEBUG FAILED: Issue found in registration process")
    print(f"{'='*70}")
