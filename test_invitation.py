#!/usr/bin/env python3
import requests
import json
import sys

# Configuration
BASE_URL = 'http://127.0.0.1:8000'
USERNAME = 'admin@example.com'  
PASSWORD = 'password123'
ORGANIZATION_ID = '392eddf8-023f-4d9f-a882-d3ea18537ad0'

def get_auth_token():
    """Get authentication token"""
    login_url = f"{BASE_URL}/api/v1/auth/jwt/create/"
    try:
        response = requests.post(login_url, json={
            'email': USERNAME,
            'password': PASSWORD
        })
        
        if response.status_code == 200:
            return response.json().get('access')
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
    
    return None

def test_invitation():
    """Test invitation functionality"""
    token = get_auth_token()
    if not token:
        print("Authentication failed, cannot proceed")
        return

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Test the invitation endpoint
    invite_url = f"{BASE_URL}/api/v1/organizations/{ORGANIZATION_ID}/invitations/"
    
    # Generate a random test email to avoid conflicts
    import random
    test_email = f"test{random.randint(1000, 9999)}@example.com"
    
    invitation_data = {
        'email': test_email,
        'role': 'member'
    }
    
    print(f"\nSending invitation to {test_email}...")
    response = requests.post(invite_url, headers=headers, json=invitation_data)
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 201:
        invitation_data = response.json()
        print(f"Invitation created successfully!")
        print(f"Token: {invitation_data.get('token', 'N/A')}")
        print(f"Expires at: {invitation_data.get('expires_at', 'N/A')}")
        
        # Check if email settings are configured
        import os
        import django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectmanagement.settings")
        django.setup()
        from django.conf import settings
        
        print(f"\nEmail Settings:")
        print(f"EMAIL_BACKEND = {settings.EMAIL_BACKEND}")
        print(f"DEFAULT_FROM_EMAIL = {settings.DEFAULT_FROM_EMAIL}")
        
        email_backend = settings.EMAIL_BACKEND
        if 'console' in email_backend.lower():
            print("\nUsing console email backend. Check Django server terminal output for the email content.")
            print("Look for lines starting with 'Content-Type:' and the HTML content of the email.")
        elif 'smtp' in email_backend.lower():
            print(f"\nEmail should be sent to {test_email}. Check your email inbox.")
            
            # Ask user if they received the email
            if input("\nDid you receive the email? (y/n): ").lower() == 'y':
                print("Email system is working correctly!")
            else:
                print("Email delivery might be failing. Check your email configuration.")
        else:
            print(f"\nUsing custom email backend: {email_backend}")
            print("Check server logs for details.")
    else:
        print(f"Failed to create invitation: {response.text}")

if __name__ == "__main__":
    test_invitation()
