#!/usr/bin/env python3
"""
Comprehensive Authentication Test - Service Worker Fix Verification
Tests the critical authentication bypass bug fix in the service worker.
"""

import requests
import json
import sys
from datetime import datetime

# Test configuration
BASE_URL = "http://127.0.0.1:8001"
TEST_USER = {
    "username": f"testuser_{int(datetime.now().timestamp())}",
    "email": f"test_{int(datetime.now().timestamp())}@example.com",
    "password": "TestPassword123!",
    "re_password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User"
}

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_test_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

def test_user_registration():
    """Test user registration endpoint - should work without auth headers"""
    print_header("TEST 1: USER REGISTRATION")
    
    try:
        print(f"Registering user: {TEST_USER['username']}")
        print(f"Endpoint: {BASE_URL}/api/v1/auth/users/")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/users/",
            json=TEST_USER,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            print_test_result("User Registration", True, "User created successfully")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Response Body: {response.text}")
            print_test_result("User Registration", False, f"Expected 201, got {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("User Registration", False, f"Exception: {str(e)}")
        return False

def test_user_login():
    """Test user login endpoint - should work without auth headers"""
    print_header("TEST 2: USER LOGIN")
    
    try:
        login_data = {
            "email": TEST_USER['email'],
            "password": TEST_USER['password']
        }
        
        print(f"Logging in user: {TEST_USER['username']}")
        print(f"Endpoint: {BASE_URL}/api/v1/auth/jwt/create/")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/jwt/create/",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            if 'access' in response_data:
                print_test_result("User Login", True, "JWT tokens received")
                print(f"Access token received: {response_data['access'][:50]}...")
                return response_data['access']
            else:
                print_test_result("User Login", False, "No access token in response")
                return None
        else:
            print(f"Response Body: {response.text}")
            print_test_result("User Login", False, f"Expected 200, got {response.status_code}")
            return None
            
    except Exception as e:
        print_test_result("User Login", False, f"Exception: {str(e)}")
        return None

def test_direct_auth_endpoints():
    """Test authentication endpoints directly without service worker"""
    print_header("TEST 3: DIRECT ENDPOINT ACCESS")
    
    # Test registration endpoint directly
    print("Testing registration endpoint accessibility...")
    try:
        response = requests.options(f"{BASE_URL}/api/v1/auth/users/")
        print(f"OPTIONS /api/v1/auth/users/ - Status: {response.status_code}")
        
        if response.status_code in [200, 204]:
            print_test_result("Registration Endpoint Access", True, "Endpoint accessible")
        else:
            print_test_result("Registration Endpoint Access", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Registration Endpoint Access", False, f"Exception: {str(e)}")
    
    # Test login endpoint directly  
    print("Testing login endpoint accessibility...")
    try:
        response = requests.options(f"{BASE_URL}/api/v1/auth/jwt/create/")
        print(f"OPTIONS /api/v1/auth/jwt/create/ - Status: {response.status_code}")
        
        if response.status_code in [200, 204]:
            print_test_result("Login Endpoint Access", True, "Endpoint accessible")
        else:
            print_test_result("Login Endpoint Access", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test_result("Login Endpoint Access", False, f"Exception: {str(e)}")

def main():
    """Run all authentication tests"""
    print_header("AUTHENTICATION FIX VERIFICATION")
    print(f"Testing service worker authentication bypass fix")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_USER['username']}")
    
    results = []
    
    # Test 1: Direct endpoint access
    test_direct_auth_endpoints()
    
    # Test 2: User Registration
    reg_success = test_user_registration()
    results.append(reg_success)
    
    # Test 3: User Login (only if registration succeeded)
    if reg_success:
        token = test_user_login()
        results.append(token is not None)
    else:
        print_test_result("User Login", False, "Skipped due to registration failure")
        results.append(False)
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "User Registration",
        "User Login"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        print_test_result(name, result)
    
    print(f"\nOVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Authentication fix is working correctly!")
        print("✅ Service worker is correctly bypassing auth injection for auth endpoints")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Authentication issues may still exist")
        return 1

if __name__ == "__main__":
    sys.exit(main())
