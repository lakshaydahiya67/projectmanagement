import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_smtp_connection():
    """Test direct SMTP connection and send a test email"""
    # Load Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
    import django
    django.setup()
    
    from django.conf import settings
    
    # Log email configuration
    logger.info(f"Email Configuration: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, TLS={settings.EMAIL_USE_TLS}")
    logger.info(f"Email User: {settings.EMAIL_HOST_USER}")
    logger.info(f"Default From Email: {settings.DEFAULT_FROM_EMAIL}")
    
    # Test email parameters
    recipient = input("Enter test recipient email: ")
    from_email = settings.DEFAULT_FROM_EMAIL
    if not from_email or from_email == '':
        from_email = settings.EMAIL_HOST_USER
        logger.info(f"Using EMAIL_HOST_USER as from_email: {from_email}")
    
    subject = "SMTP Test Email"
    text_content = "This is a test email to verify SMTP configuration."
    html_content = "<html><body><h1>Test Email</h1><p>This is a test email to verify SMTP configuration.</p></body></html>"
    
    try:
        logger.info("Testing direct SMTP connection...")
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.set_debuglevel(1)  # Enable verbose debug output
        
        if settings.EMAIL_USE_TLS:
            logger.info("Starting TLS connection...")
            server.starttls()
        
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            logger.info(f"Attempting SMTP login with user: {settings.EMAIL_HOST_USER}")
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        
        # Create test message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = recipient
        
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
        return True
    except Exception as e:
        logger.error(f"Direct SMTP test failed: {str(e)}")
        logger.exception("SMTP test exception details:")
        return False

if __name__ == "__main__":
    success = test_smtp_connection()
    if success:
        print("✅ Email test successful! Check your inbox for the test email.")
    else:
        print("❌ Email test failed. Check the logs for details.")
