"""
Test script to verify email sending functionality.
"""
import os
import sys
import django
import json
import requests
from django.conf import settings

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

# Test configuration
BASE_URL = 'http://localhost:8000'  # Update if your server is running on a different port
TEST_EMAIL = 'lakshaydahiya67@gmail.com'  # Replace with your test email

def test_direct_email():
    """Test sending a direct email using Django's send_mail."""
    print("\n=== Testing direct email sending ===")
    url = f"{BASE_URL}/api/v1/users/test/direct-email/"
    data = {'email': TEST_EMAIL}
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_password_reset_email():
    """Test sending a password reset email using the custom email class."""
    print("\n=== Testing password reset email ===")
    url = f"{BASE_URL}/api/v1/users/test/password-reset-email/"
    data = {'email': TEST_EMAIL}
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    print("Starting email sending tests...")
    print(f"Testing with email: {TEST_EMAIL}")
    
    # Test direct email first
    direct_success = test_direct_email()
    print(f"Direct email test: {'SUCCESS' if direct_success else 'FAILED'}")
    
    # Only test password reset if direct email worked
    if direct_success:
        reset_success = test_password_reset_email()
        print(f"Password reset email test: {'SUCCESS' if reset_success else 'FAILED'}")
    else:
        print("Skipping password reset email test due to direct email failure")
    
    print("\nTesting complete!")

if __name__ == "__main__":
    main()
