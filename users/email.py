"""
Email functionality for user management.
Simplified for Django's built-in authentication.
"""
import os
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings as django_settings
from django.utils.html import strip_tags
import logging
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import re

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
        email_message = EmailMultiAlternatives(
            subject,
            text_content,
            django_settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        
        # Send the email
        email_message.send(fail_silently=False)
        
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
        reset_url: The complete password reset URL
    """
    subject = 'Reset your password'
    context = {
        'user': user,
        'reset_url': reset_url,
        'site_name': 'Project Management App'
    }
    
    html_content = render_to_string('email/password_reset.html', context)
    text_content = strip_tags(html_content)
    
    try:
        email_message = EmailMultiAlternatives(
            subject,
            text_content,
            django_settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send(fail_silently=False)
        
        logger.info(f"Successfully sent password reset email to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False