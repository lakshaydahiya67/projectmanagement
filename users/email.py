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

    def get_context_data(self):
        # Get the base context data from parent class
        context = super().get_context_data()
        
        # Get the user from context
        user = context.get('user')
        
        # Add required context variables
        context['uid'] = urlsafe_base64_encode(force_bytes(user.pk))
        context['token'] = default_token_generator.make_token(user)
        context['site_name'] = django_settings.DJOSER.get('SITE_NAME')
        
        # Ensure domain is properly formatted without protocol
        domain = django_settings.DJOSER.get('DOMAIN', '')
        domain = domain.replace('http://', '').replace('https://', '').split('/')[0].strip()
        context['domain'] = domain
        
        # Determine protocol (prefer HTTPS in production)
        context['protocol'] = 'https' if django_settings.DJOSER.get('USE_HTTPS', not django_settings.DEBUG) else 'http'
        
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
        
        # Add user's full name for personalization
        context['full_name'] = user.get_full_name() or user.username
        
        logger.info(f"Generated reset URL: {context['reset_url']}")
        
        return context
        
    def send(self, to, **kwargs):
        context = self.get_context_data()
        user = context.get('user')
        
        subject = f"Reset your {context['site_name']} password"
        
        # Log email configuration
        logger.info(f"Email Configuration: HOST={django_settings.EMAIL_HOST}, PORT={django_settings.EMAIL_PORT}, TLS={django_settings.EMAIL_USE_TLS}")
        logger.info(f"Email User: {django_settings.EMAIL_HOST_USER}")
        logger.info(f"Default From Email: {django_settings.DEFAULT_FROM_EMAIL}")
        
        # Render email templates
        html_content = render_to_string(self.template_name, context)
        text_content = strip_tags(html_content)  # Strip HTML for plain text version
        
        # Log template rendering
        logger.info(f"Email template rendered with context keys: {list(context.keys())}")
        
        try:
            # Ensure 'to' is properly formatted as a valid email address
            logger.info(f"Original 'to' parameter: {to} (type: {type(to)})")
            
            if isinstance(to, (list, tuple)):
                # Extract email from list/tuple and ensure it's not empty
                recipients = [email.strip() for email in to if email and email.strip()]
                logger.info(f"Extracted recipients from list/tuple: {recipients}")
                if not recipients:
                    raise ValueError("No valid email addresses provided")
                recipient = recipients[0]  # Use the first valid email
            elif isinstance(to, str):
                # Clean up the email string
                recipient = to.strip()
                logger.info(f"Cleaned recipient string: '{recipient}'")
                if not recipient:
                    raise ValueError("Empty email address provided")
            else:
                # Handle unexpected types
                recipient = str(to).strip()
                logger.info(f"Converted recipient to string: '{recipient}'")
                if not recipient:
                    raise ValueError(f"Invalid recipient type: {type(to)}")
            
            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", recipient):
                raise ValueError(f"Invalid email format: {recipient}")
            
            # Log final recipient
            logger.info(f"Final recipient email: {recipient}")
                
            # Create the email message
            # For Gmail, it's best to use the authenticated email address as the From address
            # to avoid being marked as spam or rejected
            from_email = django_settings.EMAIL_HOST_USER
            logger.info(f"Using EMAIL_HOST_USER as from_email: {from_email}")
            
            # Add a friendly display name to the from_email
            site_name = django_settings.DJOSER.get('SITE_NAME', 'Project Management')
            friendly_from = f"{site_name} <{from_email}>"
            
            logger.info(f"Creating email with subject: '{subject}', from: '{friendly_from}', to: {[recipient]}")
            
            # Set reply-to if DEFAULT_FROM_EMAIL is different
            reply_to = None
            if django_settings.DEFAULT_FROM_EMAIL and django_settings.DEFAULT_FROM_EMAIL != from_email:
                reply_to = [django_settings.DEFAULT_FROM_EMAIL]
                logger.info(f"Setting reply-to: {reply_to}")
            
            email_message = EmailMultiAlternatives(
                subject,
                text_content,
                friendly_from,  # Use the friendly display name format
                [recipient],  # Always pass as a list with a single email
                reply_to=reply_to  # Set reply-to if specified
            )
            email_message.attach_alternative(html_content, "text/html")
            
            # Log before sending
            logger.info(f"Sending password reset email to {recipient} using backend: {django_settings.EMAIL_BACKEND}")
            
            # Try direct SMTP connection for debugging
            try:
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                
                logger.info("Testing direct SMTP connection...")
                server = smtplib.SMTP(django_settings.EMAIL_HOST, django_settings.EMAIL_PORT)
                server.set_debuglevel(1)  # Enable verbose debug output
                
                if django_settings.EMAIL_USE_TLS:
                    logger.info("Starting TLS connection...")
                    server.starttls()
                
                if django_settings.EMAIL_HOST_USER and django_settings.EMAIL_HOST_PASSWORD:
                    logger.info(f"Attempting SMTP login with user: {django_settings.EMAIL_HOST_USER}")
                    server.login(django_settings.EMAIL_HOST_USER, django_settings.EMAIL_HOST_PASSWORD)
                
                # Create test message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = "SMTP Test: " + subject
                msg['From'] = friendly_from  # Use friendly display name format
                msg['To'] = recipient
                
                # Add Reply-To header if specified
                if reply_to:
                    msg['Reply-To'] = reply_to[0]
                
                # Attach parts
                part1 = MIMEText(text_content, 'plain')
                part2 = MIMEText(html_content, 'html')
                msg.attach(part1)
                msg.attach(part2)
                
                # Send test message
                logger.info(f"Sending test SMTP message from {from_email} to {recipient}")
                server.sendmail(from_email, [recipient], msg.as_string())
                server.quit()
                logger.info("Direct SMTP test successful")
            except Exception as smtp_e:
                logger.error(f"Direct SMTP test failed: {str(smtp_e)}")
                logger.exception("SMTP test exception details:")
            
            # Send the email using Django's email system
            email_message.send(fail_silently=False)
            
            logger.info(f"Successfully sent password reset email to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to}: {str(e)}")
            # Log detailed exception for debugging
            logger.exception("Detailed password reset email error:")
            return False 