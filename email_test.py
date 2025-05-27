#!/usr/bin/env python
"""
Simple email configuration test script for Render deployment.
"""
import os
import sys
import django
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ImproperlyConfigured

def test_email_config(test_email="admin@example.com"):
    """Test email configuration."""
    try:
        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
        django.setup()
        
        print(f"Testing email configuration...")
        print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            print("✅ Console email backend configured (development mode)")
            return True
        elif settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            print(f"SMTP email backend configured")
            print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
            print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
            print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
            
            # Check if required SMTP settings are available
            if not hasattr(settings, 'EMAIL_HOST_USER') or not settings.EMAIL_HOST_USER:
                print("⚠️  EMAIL_HOST_USER not configured")
                return False
            if not hasattr(settings, 'EMAIL_HOST_PASSWORD') or not settings.EMAIL_HOST_PASSWORD:
                print("⚠️  EMAIL_HOST_PASSWORD not configured")
                return False
                
            print("✅ SMTP email backend properly configured")
            return True
        else:
            print(f"✅ Email backend configured: {settings.EMAIL_BACKEND}")
            return True
            
    except Exception as e:
        print(f"❌ Email configuration test failed: {e}")
        return False

if __name__ == "__main__":
    test_email = sys.argv[1] if len(sys.argv) > 1 else "admin@example.com"
    success = test_email_config(test_email)
    sys.exit(0 if success else 1)
