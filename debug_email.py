#!/usr/bin/env python
"""
Debug script for email settings in Django. Creates a minimal Django environment
to test email functionality without importing the full project.
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from abc.txt file
load_dotenv('abc.txt')

def check_env_variables():
    """Check all email-related environment variables"""
    env_vars = {
        'EMAIL_BACKEND': os.environ.get('EMAIL_BACKEND'),
        'EMAIL_HOST': os.environ.get('EMAIL_HOST'),
        'EMAIL_PORT': os.environ.get('EMAIL_PORT'),
        'EMAIL_USE_TLS': os.environ.get('EMAIL_USE_TLS'),
        'EMAIL_HOST_USER': os.environ.get('EMAIL_HOST_USER'),
        'EMAIL_HOST_PASSWORD': os.environ.get('EMAIL_HOST_PASSWORD'),
        'DEFAULT_FROM_EMAIL': os.environ.get('DEFAULT_FROM_EMAIL'),
    }
    
    print("\nEnvironment Variables:")
    print("======================")
    for key, value in env_vars.items():
        if key == 'EMAIL_HOST_PASSWORD' and value:
            print(f"{key}: [HIDDEN]")
        else:
            print(f"{key}: {value}")
    
    # Check for potential issues
    issues = []
    if env_vars['EMAIL_BACKEND'] != 'django.core.mail.backends.smtp.EmailBackend':
        issues.append(f"EMAIL_BACKEND is not set to SMTP backend: {env_vars['EMAIL_BACKEND']}")
    
    if not env_vars['EMAIL_HOST']:
        issues.append("EMAIL_HOST is not set")
    
    if not env_vars['EMAIL_PORT']:
        issues.append("EMAIL_PORT is not set")
    
    if not env_vars['EMAIL_HOST_USER']:
        issues.append("EMAIL_HOST_USER is not set")
    
    if not env_vars['EMAIL_HOST_PASSWORD']:
        issues.append("EMAIL_HOST_PASSWORD is not set")
    
    if issues:
        print("\nPotential Issues:")
        print("=================")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("\nNo issues found in environment variables.")

def test_smtp_connection():
    """Test SMTP connection directly"""
    host = os.environ.get('EMAIL_HOST')
    port = int(os.environ.get('EMAIL_PORT', 587))
    username = os.environ.get('EMAIL_HOST_USER')
    password = os.environ.get('EMAIL_HOST_PASSWORD')
    use_tls = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    
    print("\nTesting SMTP Connection:")
    print("=======================")
    print(f"Connecting to {host}:{port} with TLS={use_tls}")
    
    try:
        # Create SMTP connection
        smtp = smtplib.SMTP(host, port)
        smtp.set_debuglevel(1)  # Enable verbose debug output
        
        # Identify ourselves to the SMTP server
        smtp.ehlo()
        
        # If TLS is enabled, start TLS
        if use_tls:
            print("Starting TLS...")
            smtp.starttls()
            smtp.ehlo()  # Re-identify ourselves over TLS connection
        
        # Login if credentials are provided
        if username and password:
            print(f"Logging in as {username}...")
            smtp.login(username, password)
            print("Login successful!")
        
        # Close connection
        smtp.quit()
        print("SMTP connection test successful!")
        return True
    except Exception as e:
        print(f"SMTP connection failed: {str(e)}")
        return False

def send_test_email(recipient_email):
    """Send a test email using direct SMTP"""
    host = os.environ.get('EMAIL_HOST')
    port = int(os.environ.get('EMAIL_PORT', 587))
    username = os.environ.get('EMAIL_HOST_USER')
    password = os.environ.get('EMAIL_HOST_PASSWORD')
    use_tls = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    from_email = os.environ.get('DEFAULT_FROM_EMAIL', username)
    
    print("\nSending Test Email:")
    print("==================")
    print(f"From: {from_email}")
    print(f"To: {recipient_email}")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = recipient_email
    msg['Subject'] = 'Test Email from Debug Script'
    
    body = 'This is a test email sent directly using SMTP to debug email configuration issues.'
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Create SMTP connection
        smtp = smtplib.SMTP(host, port)
        smtp.set_debuglevel(1)  # Enable verbose debug output
        
        # Identify ourselves to the SMTP server
        smtp.ehlo()
        
        # If TLS is enabled, start TLS
        if use_tls:
            smtp.starttls()
            smtp.ehlo()  # Re-identify ourselves over TLS connection
        
        # Login if credentials are provided
        if username and password:
            smtp.login(username, password)
        
        # Send email
        text = msg.as_string()
        smtp.sendmail(from_email, recipient_email, text)
        
        # Close connection
        smtp.quit()
        
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

if __name__ == "__main__":
    # Check environment variables
    check_env_variables()
    
    # Test SMTP connection
    if test_smtp_connection():
        # If connection test passes, try sending an email
        if len(sys.argv) > 1:
            recipient = sys.argv[1]
        else:
            recipient = input("\nEnter recipient email address: ")
            
        send_test_email(recipient) 