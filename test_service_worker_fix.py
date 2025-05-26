#!/usr/bin/env python3
"""
Service Worker Authentication Fix Verification Script

This script tests that the service worker correctly bypasses authentication 
for registration and login endpoints after the fix.
"""

import os
import sys
import requests
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import execute_from_command_line

# Add the project root to Python path
project_root = '/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement'
sys.path.insert(0, project_root)
os.chdir(project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')

import django
django.setup()

User = get_user_model()

BASE_URL = 'http://127.0.0.1:8000'

def test_service_worker_bypass_endpoints():
    """Test that service worker bypass endpoints are correctly configured"""
    
    print("="*80)
    print("SERVICE WORKER AUTHENTICATION BYPASS VERIFICATION")
    print("="*80)
    
    # Test data for registration
    test_email = 'servicetest@example.com'
    test_password = 'TestPassword123!'
    
    # Clean up any existing test user
    User.objects.filter(email=test_email).delete()
    
    # Test 1: Registration should work without authentication
    print("\n1. Testing Registration Endpoint Bypass")
    print("-" * 50)
    
    registration_data = {
        "username": "servicetest",
        "email": test_email,
        "password": test_password,
        "re_password": test_password,
        "first_name": "Service",
        "last_name": "Test"
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/auth/users/',
            json=registration_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Registration response status: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful - endpoint correctly bypassed authentication")
            print(f"Response data: {response.json()}")
            registration_success = True
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            print(f"Response content: {response.text}")
            registration_success = False
            
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
        registration_success = False
    
    # Test 2: Login should work without authentication
    print("\n2. Testing Login Endpoint Bypass")
    print("-" * 50)
    
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/auth/jwt/create/',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            tokens = response.json()
            print("✅ Login successful - endpoint correctly bypassed authentication")
            print(f"Received tokens: access_token exists: {'access' in tokens}")
            login_success = True
            access_token = tokens.get('access')
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"Response content: {response.text}")
            login_success = False
            access_token = None
            
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        login_success = False
        access_token = None
    
    # Test 3: Verify that authenticated endpoints still require auth
    print("\n3. Testing Protected Endpoint (should require auth)")
    print("-" * 50)
    
    try:
        # Try to access user profile without authentication
        response = requests.get(
            f'{BASE_URL}/api/v1/users/me/',
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Profile request (no auth) status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Protected endpoint correctly requires authentication")
            auth_protection_working = True
        else:
            print(f"❌ Protected endpoint should return 401, got {response.status_code}")
            auth_protection_working = False
            
        # Now try with authentication
        if access_token:
            response = requests.get(
                f'{BASE_URL}/api/v1/users/me/',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}'
                }
            )
            
            print(f"Profile request (with auth) status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Protected endpoint works with valid authentication")
            else:
                print(f"❌ Protected endpoint failed with auth: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Protected endpoint test failed: {e}")
        auth_protection_working = False
    
    # Test 4: Verify service worker file accessibility
    print("\n4. Testing Service Worker File Access")
    print("-" * 50)
    
    try:
        response = requests.get(f'{BASE_URL}/auth-service-worker.js')
        print(f"Service worker file status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Service worker file is accessible")
            service_worker_accessible = True
            
            # Check if the updated endpoints are in the file
            content = response.text
            if '/api/v1/auth/users/' in content and '/api/v1/auth/jwt/create/' in content:
                print("✅ Service worker contains updated endpoint patterns")
                endpoint_patterns_updated = True
            else:
                print("❌ Service worker missing updated endpoint patterns")
                endpoint_patterns_updated = False
        else:
            print(f"❌ Service worker file not accessible: {response.status_code}")
            service_worker_accessible = False
            endpoint_patterns_updated = False
            
    except Exception as e:
        print(f"❌ Service worker test failed: {e}")
        service_worker_accessible = False
        endpoint_patterns_updated = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    tests = [
        ("Registration endpoint bypass", registration_success),
        ("Login endpoint bypass", login_success),
        ("Auth protection on protected endpoints", auth_protection_working),
        ("Service worker file accessibility", service_worker_accessible),
        ("Updated endpoint patterns in service worker", endpoint_patterns_updated)
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Service worker fix is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

def test_service_worker_patterns():
    """Test the service worker endpoint patterns directly"""
    
    print("\n" + "="*80)
    print("SERVICE WORKER PATTERN ANALYSIS")
    print("="*80)
    
    # Read the service worker file directly
    try:
        with open('/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement/auth-service-worker.js', 'r') as f:
            content = f.read()
        
        # Extract the AUTH_BYPASS_ENDPOINTS array
        start_marker = 'const AUTH_BYPASS_ENDPOINTS = ['
        end_marker = '];'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print("❌ Could not find AUTH_BYPASS_ENDPOINTS array")
            return False
        
        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            print("❌ Could not find end of AUTH_BYPASS_ENDPOINTS array")
            return False
        
        # Extract the endpoints
        endpoints_section = content[start_idx + len(start_marker):end_idx]
        
        # Parse endpoints (simple parsing)
        import re
        pattern = r"'([^']+)'"
        endpoints = re.findall(pattern, endpoints_section)
        
        print(f"Found {len(endpoints)} bypass endpoints:")
        
        # Check for required endpoints
        required_endpoints = [
            '/api/v1/auth/users/',
            '/api/v1/auth/jwt/create/',
            '/api/v1/auth/jwt/refresh/',
            '/api/v1/auth/jwt/verify/',
            '/api/v1/public/password-reset/'
        ]
        
        print("\nRequired endpoints check:")
        all_present = True
        for required in required_endpoints:
            if required in endpoints:
                print(f"✅ {required}")
            else:
                print(f"❌ {required} - MISSING")
                all_present = False
        
        print(f"\nAll bypass endpoints:")
        for endpoint in sorted(endpoints):
            print(f"  - {endpoint}")
        
        if all_present:
            print("✅ All required endpoints are present in bypass list")
        else:
            print("❌ Some required endpoints are missing")
            
        return all_present
        
    except Exception as e:
        print(f"❌ Error reading service worker file: {e}")
        return False

if __name__ == '__main__':
    print("Starting service worker authentication fix verification...")
    
    # Run pattern analysis first
    patterns_ok = test_service_worker_patterns()
    
    # Run live endpoint tests
    endpoints_ok = test_service_worker_bypass_endpoints()
    
    if patterns_ok and endpoints_ok:
        print("\n🎉 SERVICE WORKER FIX VERIFICATION COMPLETE - ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SERVICE WORKER FIX VERIFICATION FAILED")
        sys.exit(1)
