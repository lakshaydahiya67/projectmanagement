#!/usr/bin/env python
"""
A diagnostic script to test email functionality.

This script will set up Django, initialize the email backend with your
current settings, and send a test email to verify the configuration.
"""

import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

def test_email_config():
    """Print the current email configuration"""
    print("\nCurrent Email Configuration:")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * 10 if settings.EMAIL_HOST_PASSWORD else 'Not set'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

def send_test_email(to_email):
    """Send a test email"""
    print(f"\nSending test email to {to_email}...")
    
    subject = 'Test Email from Project Management App'
    message = 'This is a test email to verify your email configuration. If you receive this, your email setup is working correctly!'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [to_email]
    
    try:
        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        if result:
            print("\nSuccess! Test email sent.")
            print(f"Email sent from {from_email} to {to_email}")
            return True
        else:
            print("\nError: Email sending failed without raising an exception. Check your settings.")
            return False
    except Exception as e:
        print(f"\nError sending email: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your EMAIL_HOST and EMAIL_PORT settings")
        print("2. Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct")
        print("3. If using Gmail, ensure you've created an App Password")
        print("4. Check your firewall/network settings")
        return False

if __name__ == "__main__":
    # Display the current email config
    test_email_config()
    
    # Get the recipient email
    if len(sys.argv) > 1:
        to_email = sys.argv[1]
    else:
        to_email = input("\nEnter recipient email address: ")
    
    # Send the test email
    send_test_email(to_email) 