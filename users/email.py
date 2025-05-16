"""
Email functionality for user management.
Handles sending activation emails and password reset emails.
"""
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
            django_settings.DEFAULT_FROM_EMAIL,  # Use DEFAULT_FROM_EMAIL instead of EMAIL_HOST_USER
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Log before sending
        logger.info(f"Sending activation email to {user.email} using backend: {django_settings.EMAIL_BACKEND}")
        
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
            django_settings.DEFAULT_FROM_EMAIL,  # Use DEFAULT_FROM_EMAIL instead of EMAIL_HOST_USER
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Log before sending
        logger.info(f"Sending password reset email to {user.email} using backend: {django_settings.EMAIL_BACKEND}")
        
        # Send the email
        email.send(fail_silently=False)
        
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
        context['activation_url'] = '{protocol}://{domain}/{url}'.format(
            protocol=context['protocol'],
            domain=context['domain'],
            url=formatted_url
        )
        
        logger.info(f"Generated activation URL: {context['activation_url']}")
        
        return context


class PasswordResetEmail(email.PasswordResetEmail):
    """Custom email class for password reset"""
    template_name = 'email/password_reset.html'

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
        
        # Create the complete reset URL
        reset_url_template = django_settings.DJOSER.get('PASSWORD_RESET_CONFIRM_URL')
        
        # Debug logging
        logger.info(f"Generating password reset email for {user.email}")
        logger.info(f"Domain: {context['domain']}")
        logger.info(f"Protocol: {context['protocol']}")
        logger.info(f"URL template: {reset_url_template}")
        
        # Format the URL with uid and token
        formatted_url = reset_url_template.format(uid=context['uid'], token=context['token'])
        
        # Create the complete URL
        context['reset_url'] = '{protocol}://{domain}/{url}'.format(
            protocol=context['protocol'],
            domain=context['domain'],
            url=formatted_url
        )
        
        logger.info(f"Generated reset URL: {context['reset_url']}")
        
        return context 