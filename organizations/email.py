import os
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import OrganizationInvitation

logger = logging.getLogger(__name__)

def send_invitation_email(invitation):
    """
    Send an invitation email to join an organization
    
    Args:
        invitation: The OrganizationInvitation model instance
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    if not isinstance(invitation, OrganizationInvitation):
        logger.error("Invalid invitation object provided")
        return False
    
    # Get the base URL from settings or environment
    base_url = getattr(settings, 'BASE_URL', None)
    if not base_url:
        # Default to localhost if not configured
        port = os.environ.get('PORT', '8000')
        base_url = f"http://localhost:{port}"
    
    # Create the invitation URL
    invitation_url = f"{base_url}/organizations/{invitation.organization.id}/accept/{invitation.token}/"
    
    # Prepare email context
    context = {
        'invitation_url': invitation_url,
        'organization_name': invitation.organization.name,
        'invited_by_name': invitation.invited_by.get_full_name() or invitation.invited_by.email,
        'role_display': invitation.get_role_display(),
        'expires_at': invitation.expires_at,
        'site_name': getattr(settings, 'SITE_NAME', 'Project Management')
    }
    
    subject = f"Invitation to join {invitation.organization.name}"
    
    # Render email templates
    html_content = render_to_string('email/invitation.html', context)
    text_content = strip_tags(html_content)  # Strip HTML for plain text version
    
    try:
        # Create the email
        email_message = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        
        # Log before sending
        logger.info(f"Sending invitation email to {invitation.email} using backend: {settings.EMAIL_BACKEND}")
        
        # Send the email
        email_message.send(fail_silently=False)
        
        logger.info(f"Successfully sent invitation email to {invitation.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send invitation email to {invitation.email}: {str(e)}")
        return False
