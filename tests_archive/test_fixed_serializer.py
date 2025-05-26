#!/usr/bin/env python3
"""
Test the fixed UserCreateSerializer with Djoser format
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from users.serializers import UserCreateSerializer
from django.contrib.auth import get_user_model
import json

def test_fixed_serializer():
    """Test the fixed UserCreateSerializer with Djoser format"""
    
    print("=" * 60)
    print("TESTING FIXED UserCreateSerializer WITH DJOSER FORMAT")
    print("=" * 60)
    
    # Test data that matches what Djoser sends
    test_data = {
        "username": "test_fixed_user",
        "email": "fixed@example.com",
        "password": "TestPassword123!",
        "re_password": "TestPassword123!",  # Djoser format
        "first_name": "FixedFirst",
        "last_name": "FixedLast"
    }
    
    print(f"\n1. Testing serializer with data:")
    print(json.dumps(test_data, indent=2))
    
    # Test the serializer
    serializer = UserCreateSerializer(data=test_data)
    
    print(f"\n2. Checking if data is valid...")
    if serializer.is_valid():
        print("✅ Serializer validation passed")
        print(f"Validated data: {serializer.validated_data}")
        
        # Save the user
        try:
            user = serializer.save()
            print(f"\n3. User created successfully:")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"First name: '{user.first_name}'")
            print(f"Last name: '{user.last_name}'")
            
            if user.first_name == test_data["first_name"] and user.last_name == test_data["last_name"]:
                print("✅ First and last names correctly saved!")
                return True
            else:
                print("❌ First and last names NOT correctly saved!")
                return False
                
        except Exception as e:
            print(f"❌ Error saving user: {e}")
            return False
    else:
        print("❌ Serializer validation failed")
        print(f"Errors: {serializer.errors}")
        return False

if __name__ == "__main__":
    success = test_fixed_serializer()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 SUCCESS: Fixed UserCreateSerializer works with Djoser format!")
        print("✅ Now let's test the complete registration flow...")
    else:
        print("❌ FAILED: There's still an issue with the serializer")
    print(f"{'='*60}")
