#!/usr/bin/env python3
"""
Test script to verify Djoser configuration
"""
import os
import sys
import django

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.conf import settings
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer

def test_djoser_config():
    """Test Djoser configuration"""
    
    print("=" * 60)
    print("TESTING DJOSER CONFIGURATION")
    print("=" * 60)
    
    # Check DJOSER settings
    djoser_settings = getattr(settings, 'DJOSER', {})
    print(f"\n1. DJOSER settings:")
    for key, value in djoser_settings.items():
        print(f"  {key}: {value}")
    
    # Check what serializer is actually being used
    print(f"\n2. Checking actual serializer being used:")
    
    # Import the configured serializer
    user_create_serializer_path = djoser_settings.get('SERIALIZERS', {}).get('user_create')
    print(f"  Configured user_create serializer: {user_create_serializer_path}")
    
    if user_create_serializer_path:
        # Try to import the configured serializer
        try:
            module_path, class_name = user_create_serializer_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            serializer_class = getattr(module, class_name)
            print(f"  Successfully imported: {serializer_class}")
            print(f"  Serializer MRO: {serializer_class.__mro__}")
            
            # Check the Meta fields
            if hasattr(serializer_class, 'Meta'):
                meta = serializer_class.Meta
                print(f"  Meta.fields: {getattr(meta, 'fields', 'Not defined')}")
                print(f"  Meta.model: {getattr(meta, 'model', 'Not defined')}")
            
        except Exception as e:
            print(f"  ❌ Failed to import serializer: {e}")
    
    # Also check what the default Djoser serializer includes
    print(f"\n3. Default Djoser UserCreateSerializer:")
    print(f"  Default fields: {DjoserUserCreateSerializer.Meta.fields}")
    print(f"  Default model: {DjoserUserCreateSerializer.Meta.model}")
    
    print(f"\n4. Testing serializer instantiation:")
    try:
        # Try to create an instance of our configured serializer
        if user_create_serializer_path:
            module_path, class_name = user_create_serializer_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            serializer_class = getattr(module, class_name)
            
            # Create an instance
            serializer = serializer_class()
            print(f"  ✅ Successfully instantiated serializer")
            print(f"  Available fields: {list(serializer.fields.keys())}")
            
            # Check if first_name and last_name are in the fields
            has_first_name = 'first_name' in serializer.fields
            has_last_name = 'last_name' in serializer.fields
            print(f"  Has first_name field: {has_first_name}")
            print(f"  Has last_name field: {has_last_name}")
            
            if has_first_name and has_last_name:
                print("  ✅ Serializer includes first_name and last_name fields")
            else:
                print("  ❌ Serializer is missing first_name and/or last_name fields")
                
        else:
            print("  ❌ No user_create serializer configured")
            
    except Exception as e:
        print(f"  ❌ Failed to instantiate serializer: {e}")

if __name__ == "__main__":
    test_djoser_config()
