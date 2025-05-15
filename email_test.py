#!/usr/bin/env python
"""
A diagnostic script to test email functionality.
This script will:
1. Print current email settings
2. Attempt to send a test email
3. Report any errors in detail
"""

import os
import sys
import logging
from django.core.mail import send_mail, get_connection
from django.conf import settings

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_django():
    """Set up Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
    import django
    django.setup()

def check_env_variables():
    """Check if all required email environment variables are set"""
    required_vars = [
        'EMAIL_BACKEND',
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_USE_TLS',
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL'
    ]
    
    logger.info("Checking environment variables...")
    
    for var in required_vars:
        value = os.environ.get(var)
        # Don't log actual password values
        if var == 'EMAIL_HOST_PASSWORD' and value:
            logger.info(f"{var}: [Set - value hidden]")
        else:
            logger.info(f"{var}: {value if value else '[NOT SET]'}")
    
    # Check the settings.py values as well
    logger.info("\nDjango settings values:")
    for var in required_vars:
        if var == 'EMAIL_HOST_PASSWORD' and hasattr(settings, var) and getattr(settings, var):
            logger.info(f"{var}: [Set - value hidden]")
        else:
            if hasattr(settings, var):
                logger.info(f"{var}: {getattr(settings, var)}")
            else:
                logger.info(f"{var}: [NOT FOUND IN SETTINGS]")

def test_email_connection():
    """Test the email connection without sending an actual email"""
    try:
        logger.info("\nTesting email connection...")
        connection = get_connection()
        connection.open()
        logger.info("✅ Connection successful!")
        connection.close()
        return True
    except Exception as e:
        logger.error(f"❌ Connection failed: {str(e)}")
        logger.exception(e)
        return False

def send_test_email(recipient):
    """Send a test email"""
    try:
        logger.info(f"\nSending test email to {recipient}...")
        
        # First, make sure connection works
        if not test_email_connection():
            return False
        
        subject = 'Test Email from Project Management App'
        message = 'This is a test email to verify SMTP functionality. If you receive this, the email system is working correctly!'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [recipient]
        
        # Log what we're about to do
        logger.info(f"Subject: {subject}")
        logger.info(f"From: {from_email}")
        logger.info(f"To: {recipient_list}")
        
        # Send the email
        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        if result:
            logger.info(f"✅ Email sent successfully! Result: {result}")
            return True
        else:
            logger.error("❌ Email sending failed with no exception, but returned False")
            return False
    except Exception as e:
        logger.error(f"❌ Email sending failed: {str(e)}")
        logger.exception(e)
        return False

if __name__ == "__main__":
    # Setup Django first
    setup_django()
    
    # Check environment variables
    check_env_variables()
    
    # Ask for recipient email
    if len(sys.argv) > 1:
        recipient = sys.argv[1]
    else:
        recipient = input("\nEnter recipient email address: ")
    
    # Send test email
    if send_test_email(recipient):
        print("\n✅ Email test completed successfully!")
    else:
        print("\n❌ Email test failed. Check logs above for details.") 