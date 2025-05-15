#!/usr/bin/env python
"""
A simple script to print the email settings from the .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables from abc.txt file
load_dotenv('abc.txt')

# Email configuration keys to check
EMAIL_KEYS = [
    'EMAIL_BACKEND',
    'EMAIL_HOST',
    'EMAIL_PORT',
    'EMAIL_USE_TLS',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
    'DEFAULT_FROM_EMAIL'
]

def check_email_settings():
    """Print out the current email settings from environment variables"""
    print("\nCurrent Email Settings:")
    print("=======================")
    
    for key in EMAIL_KEYS:
        value = os.environ.get(key, '[NOT SET]')
        if key == 'EMAIL_HOST_PASSWORD' and value != '[NOT SET]':
            print(f"{key}: [HIDDEN]")
        else:
            print(f"{key}: {value}")

if __name__ == "__main__":
    check_email_settings() 