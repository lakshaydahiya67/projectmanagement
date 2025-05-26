#!/usr/bin/env python3
"""
Complete end-to-end test of the registration flow with the fix
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

import requests
import json
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def cleanup_test_user(email):
    """Clean up any existing test user"""
    try:
        with transaction.atomic():
            User.objects.filter(email=email).delete()
            print(f"✅ Cleaned up any existing user with email: {email}")
    except Exception as e:
        print(f"⚠️  Error cleaning up user: {e}")

def test_complete_registration_flow():
    """Test the complete registration flow with the fixed serializer"""
    
    print("=" * 80)
    print("COMPLETE END-TO-END REGISTRATION TEST WITH FIXED SERIALIZER")
    print("=" * 80)
    
    # Test data
    test_email = "complete_test@example.com"
    test_data = {
        "username": "complete_test_user",
        "email": test_email,
        "password": "TestPassword123!",
        "re_password": "TestPassword123!",
        "first_name": "CompleteFirst",
        "last_name": "CompleteLast"
    }
    
    # Clean up any existing test user
    cleanup_test_user(test_email)
    
    print(f"\n1. REGISTRATION - Testing API call to /api/v1/auth/users/")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Registration API call
        response = requests.post(
            'http://localhost:8000/api/v1/auth/users/',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration API call successful")
            
            # Check if user was created in database
            try:
                user = User.objects.get(email=test_email)
                print(f"\n2. DATABASE CHECK - User found in database:")
                print(f"   Username: {user.username}")
                print(f"   Email: {user.email}")
                print(f"   First name: '{user.first_name}'")
                print(f"   Last name: '{user.last_name}'")
                print(f"   Is active: {user.is_active}")
                
                if user.first_name == test_data["first_name"] and user.last_name == test_data["last_name"]:
                    print("✅ First and last names correctly saved in database!")
                    
                    # Test activation (since SEND_ACTIVATION_EMAIL = True)
                    if not user.is_active:
                        print(f"\n3. ACTIVATION - User needs activation, activating...")
                        user.is_active = True
                        user.save()
                        print("✅ User activated")
                    else:
                        print(f"\n3. ACTIVATION - User is already active")
                    
                    # Test login
                    print(f"\n4. LOGIN TEST - Testing login with email/password")
                    login_data = {
                        "email": test_email,
                        "password": "TestPassword123!"
                    }
                    
                    login_response = requests.post(
                        'http://localhost:8000/api/v1/auth/token/login/',
                        json=login_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    print(f"Login Status: {login_response.status_code}")
                    print(f"Login Response: {login_response.text}")
                    
                    if login_response.status_code == 200:
                        print("✅ Login successful")
                        
                        # Get auth token
                        token_data = login_response.json()
                        auth_token = token_data.get('auth_token')
                        
                        if auth_token:
                            print(f"✅ Auth token received: {auth_token[:20]}...")
                            
                            # Test profile API call
                            print(f"\n5. PROFILE API TEST - Testing /api/v1/users/me/")
                            
                            profile_response = requests.get(
                                'http://localhost:8000/api/v1/users/me/',
                                headers={
                                    'Authorization': f'Token {auth_token}',
                                    'Content-Type': 'application/json'
                                }
                            )
                            
                            print(f"Profile Status: {profile_response.status_code}")
                            print(f"Profile Response: {profile_response.text}")
                            
                            if profile_response.status_code == 200:
                                print("✅ Profile API call successful")
                                
                                profile_data = profile_response.json()
                                api_first_name = profile_data.get('first_name', '')
                                api_last_name = profile_data.get('last_name', '')
                                
                                print(f"\n6. FINAL VERIFICATION:")
                                print(f"   API first_name: '{api_first_name}'")
                                print(f"   API last_name: '{api_last_name}'")
                                print(f"   Expected first_name: '{test_data['first_name']}'")
                                print(f"   Expected last_name: '{test_data['last_name']}'")
                                
                                if api_first_name == test_data["first_name"] and api_last_name == test_data["last_name"]:
                                    print("\n🎉 SUCCESS! Complete registration flow works correctly!")
                                    print("✅ First and last names are properly saved and returned by API")
                                    return True
                                else:
                                    print(f"\n❌ FAILED: Names don't match in API response")
                                    return False
                            else:
                                print(f"❌ Profile API call failed")
                                return False
                        else:
                            print(f"❌ No auth token received")
                            return False
                    else:
                        print(f"❌ Login failed")
                        return False
                else:
                    print(f"❌ First and last names NOT correctly saved in database!")
                    print(f"   Expected: '{test_data['first_name']}' '{test_data['last_name']}'")
                    print(f"   Got: '{user.first_name}' '{user.last_name}'")
                    return False
                    
            except User.DoesNotExist:
                print("❌ User not found in database after registration")
                return False
            except Exception as e:
                print(f"❌ Error checking database: {e}")
                return False
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure Django server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_registration_flow()
    
    print(f"\n{'='*80}")
    if success:
        print("🎉 COMPLETE SUCCESS: Registration flow fixed and working perfectly!")
        print("✅ First and last names are now properly saved and displayed")
    else:
        print("❌ Test failed - there may still be issues to investigate")
    print(f"{'='*80}")
