#!/usr/bin/env python
"""
Script to generate secure keys for Django and JWT.
Run this script to generate a secure SECRET_KEY and JWT_SIGNING_KEY for your production environment.
"""

import secrets
import string
import os
import re

def generate_secure_key(length=64):
    """Generate a cryptographically secure random string for use as a secret key."""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*()-_=+[]{}|;:,.<>?'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def update_env_file(env_path, django_key, jwt_key):
    """Update the .env file with secure keys."""
    if not os.path.exists(env_path):
        print(f"Error: {env_path} does not exist. Please create it first by copying env-example.")
        return False
    
    # Read the current content of the .env file
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Replace the insecure keys with secure ones using regex to match the exact lines
    content = re.sub(r'DJANGO_SECRET_KEY=.*', f'DJANGO_SECRET_KEY={django_key}', content)
    content = re.sub(r'JWT_SIGNING_KEY=.*', f'JWT_SIGNING_KEY={jwt_key}', content)
    
    # Write the updated content back to the .env file
    with open(env_path, 'w') as f:
        f.write(content)
    
    return True

def check_env_exists():
    """Check if .env file exists and create it from env-example if it doesn't."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    env_example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'env-example')
    
    if not os.path.exists(env_path) and os.path.exists(env_example_path):
        print("The .env file doesn't exist. Creating it from env-example...")
        with open(env_example_path, 'r') as src:
            with open(env_path, 'w') as dest:
                dest.write(src.read())
        print(".env file created from env-example.")
        return True
    
    return os.path.exists(env_path)

if __name__ == "__main__":
    # Generate secure keys
    django_secret_key = generate_secure_key()
    jwt_signing_key = generate_secure_key()
    
    print("\nGenerated secure keys for your production environment:")
    print("\nDJANGO_SECRET_KEY:")
    print(django_secret_key)
    print("\nJWT_SIGNING_KEY:")
    print(jwt_signing_key)
    
    # Check if .env exists and create it if needed
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if check_env_exists():
        answer = input("\nDo you want to update your .env file with these keys? (y/n): ")
        if answer.lower() in ('y', 'yes'):
            if update_env_file(env_path, django_secret_key, jwt_signing_key):
                print("\nSuccessfully updated .env file with secure keys!")
                print("\nRestart your application for the changes to take effect.")
            else:
                print("\nFailed to update .env file.")
        else:
            print("\nKeys not applied to .env file. Please update your .env file manually.")
    else:
        print(f"\n.env file not found at {env_path} and couldn't be created from env-example. Please create it manually.")
    
    print("\nRemember to keep these keys secret and never commit them to version control!") 