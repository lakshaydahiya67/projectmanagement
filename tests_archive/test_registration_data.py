#!/usr/bin/env python3
"""
Test to verify the registration issue with first_name and last_name
"""
import requests
import json
import random
import string

def generate_random_user():
    """Generate random user data for testing"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return {
        'username': f'testuser_{suffix}',
        'email': f'test_{suffix}@example.com',
        'password': 'TestPass123!',
        're_password': 'TestPass123!',
        'first_name': f'Test_{suffix}',
        'last_name': f'User_{suffix}'
    }

def test_registration_data_persistence():
    """Test if registration data is properly saved and retrievable"""
    print("🔍 Testing registration data persistence...")
    
    # Generate test user
    user_data = generate_random_user()
    print(f"📝 Creating user: {user_data['username']}")
    print(f"   First name: {user_data['first_name']}")
    print(f"   Last name: {user_data['last_name']}")
    
    # Step 1: Register user
    print("\n📋 Step 1: Registering user...")
    try:
        response = requests.post('http://localhost:8000/api/v1/auth/users/', 
                               json=user_data,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 201:
            print("✅ Registration successful")
            user_id = response.json().get('id')
            print(f"   User ID: {user_id}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Registration request failed: {e}")
        return False
    
    # Step 2: Login to get JWT token
    print("\n🔐 Step 2: Logging in...")
    try:
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        response = requests.post('http://localhost:8000/api/v1/auth/jwt/create/', 
                               json=login_data,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access')
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return False
    
    # Step 3: Get user profile data
    print("\n👤 Step 3: Retrieving user profile...")
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get('http://localhost:8000/api/v1/users/me/', headers=headers)
        
        if response.status_code == 200:
            profile_data = response.json()
            print("✅ Profile retrieval successful")
            print(f"   API Response: {json.dumps(profile_data, indent=2)}")
            
            # Check if first_name and last_name are populated
            api_first_name = profile_data.get('first_name', '')
            api_last_name = profile_data.get('last_name', '')
            
            print(f"\n🧪 Data Comparison:")
            print(f"   Expected first_name: '{user_data['first_name']}'")
            print(f"   API first_name: '{api_first_name}'")
            print(f"   Expected last_name: '{user_data['last_name']}'")
            print(f"   API last_name: '{api_last_name}'")
            
            if api_first_name == user_data['first_name'] and api_last_name == user_data['last_name']:
                print("✅ First and last names match - no issue found")
                return True
            else:
                print("❌ First and last names don't match - ISSUE CONFIRMED")
                return False
        else:
            print(f"❌ Profile retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Profile request failed: {e}")
        return False

def main():
    """Main test execution"""
    print("=" * 60)
    print("🧪 REGISTRATION DATA PERSISTENCE TEST")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        print("✅ Server is accessible")
    except requests.RequestException:
        print("❌ Server is not accessible. Please start the Django server:")
        print("   python manage.py runserver 8000")
        return
    
    # Run the test
    success = test_registration_data_persistence()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST PASSED: Registration data persistence is working correctly")
    else:
        print("❌ TEST FAILED: Registration data is not being saved/retrieved properly")
        print("🔧 This confirms the reported issue with first_name and last_name")
    print("=" * 60)

if __name__ == "__main__":
    main()
