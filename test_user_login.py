#!/usr/bin/env python3
import os
import django
import sys
import getpass

# Add the project directory to Python path
sys.path.insert(0, '/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

def main():
    """List all users and test authentication"""
    print("Available users:")
    for user in User.objects.all()[:10]:  # Limit to 10 users
        print(f"- Username: {user.username}, Email: {user.email}")
    
    print("\nTesting default passwords:")
    test_passwords = ['password123', 'admin', 'password', 'testpassword']
    
    for username in ['lakshay', 'admin']:
        for password in test_passwords:
            user = authenticate(username=username, password=password)
            if user:
                print(f"✅ Successfully authenticated {username} with password '{password}'")
            else:
                print(f"❌ Failed to authenticate {username} with password '{password}'")

if __name__ == '__main__':
    print("🔍 TESTING USER AUTHENTICATION")
    print("=" * 60)
    main()
