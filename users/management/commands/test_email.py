from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Test email functionality by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument('recipient', help='Recipient email address')

    def handle(self, *args, **options):
        recipient = options['recipient']
        
        # Display current email settings
        self.stdout.write(self.style.NOTICE('Current Email Settings:'))
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        # Also check environment variables to ensure they're loaded
        self.stdout.write(self.style.NOTICE('\nEnvironment Variables:'))
        self.stdout.write(f"EMAIL_BACKEND: {os.environ.get('EMAIL_BACKEND')}")
        self.stdout.write(f"EMAIL_HOST: {os.environ.get('EMAIL_HOST')}")
        
        # Test connection first
        self.stdout.write(self.style.NOTICE('\nTesting email connection...'))
        try:
            connection = get_connection()
            connection.open()
            self.stdout.write(self.style.SUCCESS('Connection successful!'))
            connection.close()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Connection failed: {str(e)}'))
            return
        
        # Now try sending an email
        self.stdout.write(self.style.NOTICE(f'\nSending test email to {recipient}...'))
        try:
            subject = 'Test Email from Django Management Command'
            message = 'This is a test email to verify the email functionality is working correctly in Django.'
            from_email = settings.DEFAULT_FROM_EMAIL
            
            result = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            if result:
                self.stdout.write(self.style.SUCCESS('Email sent successfully!'))
            else:
                self.stdout.write(self.style.ERROR('Email sending failed with no exception, but returned 0'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Email sending failed: {str(e)}')) 