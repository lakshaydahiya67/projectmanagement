"""
Email functionality for user management.
Handles sending activation emails and password reset emails.
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
from djoser import email
from djoser.conf import settings as djoser_settings
import re

# Set up logging
logger = logging.getLogger(__name__)

# Debug message to verify module loading
print("\n\n[MODULE LOAD] users.email module is being imported\n\n")
logger.critical("users.email module is being imported")

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
            django_settings.DEFAULT_FROM_EMAIL,  # Use DEFAULT_FROM_EMAIL instead of EMAIL_HOST_USER
            [user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        
        # Log before sending
        logger.info(f"Sending activation email to {user.email} using backend: {django_settings.EMAIL_BACKEND}")
        
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
        email_message = EmailMultiAlternatives(
            subject,
            text_content,
            django_settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        
        # Log before sending
        logger.info(f"Sending password reset email to {user.email}")
        
        # Send the email
        email_message.send(fail_silently=False)
        
        logger.info(f"Successfully sent password reset email to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

class ActivationEmail(email.ActivationEmail):
    """Custom email class for user activation"""
    template_name = 'email/activation.html'

    def get_context_data(self):
        # Get the base context data from parent class
        context = super().get_context_data()
        
        # Get the user from context
        user = context.get('user')
        
        # Add required context variables
        context['uid'] = urlsafe_base64_encode(force_bytes(user.pk))
        context['token'] = default_token_generator.make_token(user)
        context['site_name'] = django_settings.DJOSER.get('SITE_NAME')
        context['domain'] = django_settings.DJOSER.get('DOMAIN')
        context['protocol'] = 'https' if django_settings.DJOSER.get('USE_HTTPS', False) else 'http'
        
        # Create the complete activation URL
        activation_url_template = django_settings.DJOSER.get('ACTIVATION_URL')
        
        # Debug logging
        logger.info(f"Generating activation email for {user.email}")
        logger.info(f"Domain: {context['domain']}")
        logger.info(f"Protocol: {context['protocol']}")
        logger.info(f"URL template: {activation_url_template}")
        
        # Format the URL with uid and token
        formatted_url = activation_url_template.format(uid=context['uid'], token=context['token'])
        
        # Create the complete URL
        # Make sure we're using the correct domain with port for local development
        domain = context['domain']
        
        # Fix: Handle comma-separated domain list by taking only the first domain
        if ',' in domain:
            # Split by comma and take the first domain
            domain = domain.split(',')[0].strip()
            logger.info(f"Multiple domains detected, using first domain: {domain}")
        
        # If we're running locally on port 8000, ensure the port is included
        if domain == 'localhost' and os.environ.get('PORT', '8000') != '80':
            domain = f"localhost:{os.environ.get('PORT', '8000')}"
        
        context['activation_url'] = '{protocol}://{domain}/{url}'.format(
            protocol=context['protocol'],
            domain=domain,
            url=formatted_url
        )
        
        logger.info(f"Generated activation URL: {context['activation_url']}")
        
        return context
        
    def send(self, to, **kwargs):
        context = self.get_context_data()
        user = context.get('user')
        
        subject = f"Activate your {context['site_name']} account"
        
        # Render email templates
        html_content = render_to_string(self.template_name, context)
        text_content = strip_tags(html_content)  # Strip HTML for plain text version
        
        try:
            # Handle different types of 'to' parameter
            recipient = to
            if isinstance(to, list):
                recipient = to[0]  # Get the first email if it's a list
            
            # Create the email message
            email_message = EmailMultiAlternatives(
                subject,
                text_content,
                django_settings.DEFAULT_FROM_EMAIL,
                [recipient]  # Always pass as a list with a single email
            )
            email_message.attach_alternative(html_content, "text/html")
            
            # Log before sending
            logger.info(f"Sending activation email to {recipient} using backend: {django_settings.EMAIL_BACKEND}")
            
            # Send the email
            email_message.send(fail_silently=False)
            
            logger.info(f"Successfully sent activation email to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send activation email to {to}: {str(e)}")
            return False


class PasswordResetEmail(email.PasswordResetEmail):
    """Custom email class for password reset"""
    template_name = 'email/password_reset.html'

    def __init__(self, request=None, context=None, *args, **kwargs):
        # Initialize with parent class
        super().__init__(request, context, *args, **kwargs)
        logger.info(f"PasswordResetEmail initialized with request={request}")

    def get_context_data(self):
        logger.info("PasswordResetEmail.get_context_data called")
        
        # Get the base context data from parent class
        try:
            context = super().get_context_data()
            logger.info(f"Base context data retrieved successfully")
        except Exception as e:
            logger.error(f"Error in super().get_context_data(): {str(e)}")
            context = {}
        
        # Get the user from context
        user = context.get('user')
        if not user:
            logger.error("No user found in context!")
            return context
            
        logger.info(f"Processing password reset for user: {user.email}")
        
        try:
            # Add required context variables
            context['uid'] = urlsafe_base64_encode(force_bytes(user.pk))
            context['token'] = default_token_generator.make_token(user)
            
            # Ensure domain is properly formatted without protocol
            domain = context.get('domain', '')
            logger.debug(f"Original domain from context: '{domain}'")
            
            # Fix: Handle comma-separated domain list by taking only the first domain
            if ',' in domain:
                # Split by comma and take the first domain
                domain = domain.split(',')[0].strip()
                logger.debug(f"Multiple domains detected, using first domain: '{domain}'")
            
            # If we're running locally on port 8000, ensure the port is included
            if domain == 'localhost' and os.environ.get('PORT', '8000') != '80':
                domain = f"localhost:{os.environ.get('PORT', '8000')}"
                context['domain'] = domain
                logger.debug(f"Updated domain with port: '{domain}'")
                
            # Format the URL with uid and token
            url_template = django_settings.DJOSER.get('PASSWORD_RESET_CONFIRM_URL')
            logger.debug(f"URL template from settings: '{url_template}'")
            
            formatted_url = url_template.format(uid=context['uid'], token=context['token'])
            logger.debug(f"Formatted URL: '{formatted_url}'")
            
            # Create the complete reset URL
            context['url'] = formatted_url  # This is used by the parent class
            
            protocol = context.get('protocol', 'http')
            logger.debug(f"Protocol: '{protocol}'")
            
            # Force HTTP for localhost
            if domain == 'localhost' or '127.0.0.1' in domain:
                protocol = 'http'
                logger.debug(f"Forced protocol to HTTP for localhost")
            
            context['reset_url'] = '{protocol}://{domain}/{url}'.format(
                protocol=protocol,
                domain=domain,
                url=formatted_url
            )
            logger.debug(f"Complete reset URL: '{context['reset_url']}'")
            
            # Add user's full name for personalization
            context['full_name'] = user.get_full_name() or user.username
            logger.debug(f"User full name: '{context['full_name']}'")
            
            # Add site_name to context if not present
            if 'site_name' not in context:
                context['site_name'] = django_settings.DJOSER.get('SITE_NAME', 'Project Management')
                logger.debug(f"Added site_name to context: {context['site_name']}")
            
            return context
        except Exception as e:
            logger.error(f"Error in get_context_data: {str(e)}")
            logger.exception("Exception details:")
            return context
        
    def send(self, to, *args, **kwargs):
        logger.info(f"PasswordResetEmail.send() called with recipient: {to}")
        
        try:
            # Handle different types of 'to' parameter
            recipient = to
            if isinstance(to, list) or isinstance(to, tuple):
                recipient = to[0]  # Get the first email if it's a list/tuple
                logger.info(f"Extracted first recipient from list/tuple: {recipient}")
            elif not isinstance(to, str):
                recipient = str(to).strip()
                logger.info(f"Converted non-string recipient to string: {recipient}")
            
            # Get context for email
            context = self.get_context_data()
            
            # Render email templates
            html_content = render_to_string(self.template_name, context)
            text_content = strip_tags(html_content)  # Strip HTML for plain text version
            
            logger.info(f"Sending password reset email to {recipient}")
            logger.debug(f"Email backend: {django_settings.EMAIL_BACKEND}")
                
            # Create the email message
            email_message = EmailMultiAlternatives(
                subject=f"Reset your {django_settings.DJOSER.get('SITE_NAME', 'Project Management')} password",
                body=text_content,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                to=[recipient]
            )
            
            # Attach HTML version
            email_message.attach_alternative(html_content, "text/html")
            
            # Send the email
            email_message.send(fail_silently=False)
            
            logger.info(f"Successfully sent password reset email to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to}: {str(e)}")
            logger.exception("Password reset email error:")
            # Try parent class method as fallback
            try:
                parent_result = super().send([recipient] if isinstance(recipient, str) else to, *args, **kwargs)
                logger.info(f"Fallback to parent class send method: {parent_result}")
                return True
            except Exception as parent_e:
                logger.error(f"Parent class send method also failed: {str(parent_e)}")
                return False