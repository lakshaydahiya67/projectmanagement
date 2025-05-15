"""
Email functionality for user management.
Handles sending activation emails and password reset emails.
"""
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
import logging

# Set up logging
logger = logging.getLogger(__name__)

def send_activation_email(user, activation_url):
    """
    Send an activation email to a newly registered user.
    
    Args:
        user: The user model instance
        activation_url: The full URL for account activation
    """
    subject = 'Activate your account'
    context = {
        'user': user,
        'activation_url': activation_url,
        'site_name': 'Project Management App'
    }
    
    # Render email templates
    html_content = render_to_string('email/activation.html', context)
    text_content = strip_tags(html_content)  # Strip HTML for plain text version
    
    try:
        # Create the email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,  # Use DEFAULT_FROM_EMAIL instead of EMAIL_HOST_USER
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Log before sending
        logger.info(f"Sending activation email to {user.email} using backend: {settings.EMAIL_BACKEND}")
        
        # Send the email
        email.send(fail_silently=False)
        
        logger.info(f"Successfully sent activation email to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send activation email to {user.email}: {str(e)}")
        return False

def send_password_reset_email(user, reset_url):
    """
    Send a password reset email to a user.
    
    Args:
        user: The user model instance
        reset_url: The full URL for password reset
    """
    subject = 'Reset your password'
    context = {
        'user': user,
        'reset_url': reset_url,
        'site_name': 'Project Management App'
    }
    
    # Render email templates
    html_content = render_to_string('email/password_reset.html', context)
    text_content = strip_tags(html_content)  # Strip HTML for plain text version
    
    try:
        # Create the email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,  # Use DEFAULT_FROM_EMAIL instead of EMAIL_HOST_USER
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Log before sending
        logger.info(f"Sending password reset email to {user.email} using backend: {settings.EMAIL_BACKEND}")
        
        # Send the email
        email.send(fail_silently=False)
        
        logger.info(f"Successfully sent password reset email to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False 