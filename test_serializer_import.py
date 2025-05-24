#!/usr/bin/env python3
"""
Test script to verify our custom serializer is being imported correctly
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

def test_serializer_import():
    """Test that our custom serializer can be imported and used"""
    
    print("Testing custom serializer import and configuration...")
    
    # Test 1: Check Djoser settings
    from django.conf import settings
    djoser_settings = getattr(settings, 'DJOSER', {})
    
    print(f"DJOSER settings: {djoser_settings}")
    print(f"User create serializer: {djoser_settings.get('SERIALIZERS', {}).get('user_create')}")
    
    # Test 2: Try to import our custom serializer directly
    try:
        from users.serializers import UserCreateSerializer
        print(f"✅ Successfully imported UserCreateSerializer: {UserCreateSerializer}")
        print(f"   - MRO: {UserCreateSerializer.__mro__}")
        print(f"   - Fields in Meta: {getattr(UserCreateSerializer.Meta, 'fields', 'No fields')}")
    except Exception as e:
        print(f"❌ Failed to import UserCreateSerializer: {e}")
        return False
    
    # Test 3: Try to instantiate the serializer
    try:
        serializer = UserCreateSerializer()
        print(f"✅ Successfully instantiated serializer")
        print(f"   - Available fields: {list(serializer.fields.keys())}")
        
        # Check if first_name and last_name are in the fields
        if 'first_name' in serializer.fields and 'last_name' in serializer.fields:
            print("✅ first_name and last_name are in serializer fields")
        else:
            print("❌ first_name and/or last_name missing from serializer fields")
            
    except Exception as e:
        print(f"❌ Failed to instantiate serializer: {e}")
        return False
    
    # Test 4: Check if Djoser can load our serializer
    try:
        from djoser.conf import settings as djoser_conf
        user_create_serializer_class = djoser_conf.SERIALIZERS['user_create']
        print(f"✅ Djoser user_create serializer class: {user_create_serializer_class}")
        
        # Try to import the class that Djoser is using
        from django.utils.module_loading import import_string
        actual_serializer_class = import_string(user_create_serializer_class)
        print(f"✅ Actual serializer class loaded by Djoser: {actual_serializer_class}")
        print(f"   - Same as our custom class: {actual_serializer_class == UserCreateSerializer}")
        
    except Exception as e:
        print(f"❌ Failed to load Djoser serializer: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_serializer_import()
    if success:
        print("\n🎉 All serializer import tests passed!")
    else:
        print("\n❌ Serializer import tests failed!")
