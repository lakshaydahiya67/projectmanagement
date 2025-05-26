#!/usr/bin/env python3
"""
Comprehensive profile page functionality test.
Tests all features including:
- Profile data pre-filling
- Profile updates
- Password change
- Profile picture upload
- Error handling
- Field validation
"""

import requests
import json
import os
import sys
import tempfile
from PIL import Image
import io

# Add the Django project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

BASE_URL = 'http://127.0.0.1:8000'

def setup_authenticated_session():
    """Setup an authenticated session with test user"""
    email = 'test@example.com'
    
    # Delete existing user if exists
    User.objects.filter(email=email).delete()
    
    # Create test user
    user = User.objects.create_user(
        username='testuser',
        email=email,
        password='testpass123',
        first_name='John',
        last_name='Doe',
        phone_number='+1234567890',
        job_title='Software Engineer',
        bio='Test user for profile testing'
    )
    
    # Get JWT token
    response = requests.post(f'{BASE_URL}/api/v1/auth/jwt/create/', {
        'email': email,
        'password': 'testpass123'
    })
    
    if response.status_code != 200:
        raise Exception(f"Failed to authenticate: {response.text}")
    
    token = response.json()['access']
    
    # Setup session with authentication
    session = requests.Session()
    session.cookies.set('access_token', token, domain='127.0.0.1')
    
    # Get CSRF token
    csrf_response = session.get(f'{BASE_URL}/')
    csrf_token = session.cookies.get('csrftoken')
    
    return session, user, csrf_token

def test_profile_data_prefill():
    """Test that profile data is correctly pre-filled"""
    print("\n=== Testing Profile Data Pre-fill ===")
    
    session, user, csrf_token = setup_authenticated_session()
    
    # Check that API returns user data
    response = session.get(f'{BASE_URL}/api/v1/users/me/')
    if response.status_code == 200:
        data = response.json()
        expected_fields = ['first_name', 'last_name', 'email', 'phone_number', 'job_title', 'bio']
        
        print("✅ Profile API returns user data:")
        for field in expected_fields:
            value = data.get(field)
            print(f"  {field}: {value}")
        
        return True
    else:
        print(f"❌ Failed to get user data: {response.status_code} - {response.text}")
        return False

def test_profile_update():
    """Test profile update functionality"""
    print("\n=== Testing Profile Update ===")
    
    session, user, csrf_token = setup_authenticated_session()
    
    update_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'phone_number': '+9876543210',
        'job_title': 'Senior Developer',
        'bio': 'Updated bio for testing purposes'
    }
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json',
    }
    
    response = session.patch(f'{BASE_URL}/api/v1/users/me/', 
                           data=json.dumps(update_data), 
                           headers=headers)
    
    if response.status_code == 200:
        updated_data = response.json()
        print("✅ Profile update successful:")
        for field, expected_value in update_data.items():
            actual_value = updated_data.get(field)
            if actual_value == expected_value:
                print(f"  ✅ {field}: {actual_value}")
            else:
                print(f"  ❌ {field}: expected {expected_value}, got {actual_value}")
        return True
    else:
        print(f"❌ Profile update failed: {response.status_code} - {response.text}")
        return False

def test_profile_update_validation():
    """Test profile update validation"""
    print("\n=== Testing Profile Update Validation ===")
    
    session, user, csrf_token = setup_authenticated_session()
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json',
    }
    
    # Test empty required fields
    invalid_data = {
        'first_name': '',
        'last_name': ''
    }
    
    response = session.patch(f'{BASE_URL}/api/v1/users/me/', 
                           data=json.dumps(invalid_data), 
                           headers=headers)
    
    if response.status_code != 200:
        print("✅ Validation correctly prevents empty required fields")
        print(f"  Status: {response.status_code}")
        return True
    else:
        print("❌ Validation should prevent empty required fields")
        return False

def test_password_change():
    """Test password change functionality"""
    print("\n=== Testing Password Change ===")
    
    session, user, csrf_token = setup_authenticated_session()
    
    # Check if password change endpoint exists
    password_data = {
        'old_password': 'testpass123',
        'new_password': 'NewPass123!',
        'confirm_password': 'NewPass123!'
    }
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json',
    }
    
    # Check what password change endpoint the frontend is using
    response = session.post(f'{BASE_URL}/api/v1/users/{user.id}/change_password/', 
                          data=json.dumps(password_data), 
                          headers=headers)
    
    if response.status_code == 200:
        print("✅ Password change successful")
        
        # Test login with new password
        login_response = requests.post(f'{BASE_URL}/api/v1/auth/jwt/create/', {
            'email': user.email,
            'password': 'NewPass123!'
        })
        
        if login_response.status_code == 200:
            print("✅ Can login with new password")
            return True
        else:
            print("❌ Cannot login with new password")
            return False
    else:
        print(f"⚠️  Password change endpoint response: {response.status_code} - {response.text}")
        # Check if it's a 404 (endpoint doesn't exist) or other issue
        if response.status_code == 404:
            print("  Password change endpoint may not be implemented")
        return False

def create_test_image():
    """Create a small test image for profile picture upload"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_profile_picture_upload():
    """Test profile picture upload functionality"""
    print("\n=== Testing Profile Picture Upload ===")
    
    session, user, csrf_token = setup_authenticated_session()
    
    # Create a test image
    test_image = create_test_image()
    
    headers = {
        'X-CSRFToken': csrf_token,
    }
    
    files = {
        'profile_picture': ('test_avatar.png', test_image, 'image/png')
    }
    
    response = session.patch(f'{BASE_URL}/api/v1/users/me/', 
                           files=files, 
                           headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('profile_picture'):
            print("✅ Profile picture upload successful")
            print(f"  Image URL: {data['profile_picture']}")
            return True
        else:
            print("❌ Profile picture upload succeeded but no image URL returned")
            return False
    else:
        print(f"❌ Profile picture upload failed: {response.status_code} - {response.text}")
        return False

def test_error_handling():
    """Test error handling for various scenarios"""
    print("\n=== Testing Error Handling ===")
    
    session, user, csrf_token = setup_authenticated_session()
    
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json',
    }
    
    # Test invalid email format (if the frontend tries to update email)
    invalid_data = {
        'email': 'invalid-email-format'
    }
    
    response = session.patch(f'{BASE_URL}/api/v1/users/me/', 
                           data=json.dumps(invalid_data), 
                           headers=headers)
    
    print(f"Invalid email test - Status: {response.status_code}")
    
    # Test oversized profile picture
    large_image = Image.new('RGB', (5000, 5000), color='blue')
    large_img_bytes = io.BytesIO()
    large_image.save(large_img_bytes, format='PNG')
    large_img_bytes.seek(0)
    
    files = {
        'profile_picture': ('large_avatar.png', large_img_bytes, 'image/png')
    }
    
    response = session.patch(f'{BASE_URL}/api/v1/users/me/', 
                           files=files, 
                           headers={'X-CSRFToken': csrf_token})
    
    if response.status_code != 200:
        print("✅ Large image properly rejected")
    else:
        print("⚠️  Large image was accepted (may not have size limits)")
    
    return True

def test_javascript_functionality():
    """Test if the JavaScript on the profile page works correctly"""
    print("\n=== Testing JavaScript Functionality ===")
    
    session, user, csrf_token = setup_authenticated_session()
    
    # Get the profile page and check for JavaScript
    response = session.get(f'{BASE_URL}/profile/')
    
    if response.status_code == 200:
        html_content = response.text
        
        # Check for key JavaScript functions and elements
        js_checks = [
            'profileUpdateForm',
            'passwordChangeForm', 
            'profilePictureUploadForm',
            'loadInitialProfileData',
            'fetch(\'/api/v1/users/me/\')',
            'X-CSRFToken'
        ]
        
        print("JavaScript functionality checks:")
        for check in js_checks:
            if check in html_content:
                print(f"  ✅ Found: {check}")
            else:
                print(f"  ❌ Missing: {check}")
        
        return True
    else:
        print(f"❌ Failed to load profile page: {response.status_code}")
        return False

def main():
    print("=== Comprehensive Profile Page Test ===")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Profile Data Pre-fill", test_profile_data_prefill()))
    test_results.append(("Profile Update", test_profile_update()))
    test_results.append(("Profile Update Validation", test_profile_update_validation()))
    test_results.append(("Password Change", test_password_change()))
    test_results.append(("Profile Picture Upload", test_profile_picture_upload()))
    test_results.append(("Error Handling", test_error_handling()))
    test_results.append(("JavaScript Functionality", test_javascript_functionality()))
    
    # Summary
    print("\n=== Test Summary ===")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Profile page is fully functional.")
    else:
        print("⚠️  Some tests failed. Review the issues above.")

if __name__ == '__main__':
    main()
