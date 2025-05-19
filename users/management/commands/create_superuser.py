import os
import getpass
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.management import call_command

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser with the specified email and password'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Superuser username')
        parser.add_argument('--email', type=str, help='Superuser email')
        parser.add_argument('--password', type=str, help='Superuser password')
        parser.add_argument('--noinput', '--no-input', action='store_false', dest='interactive',
                          help='Tells Django to NOT prompt the user for input of any kind.')

    def get_input_data(self, field_name, prompt, default=None):
        """Get input data from user or use default if provided."""
        if default:
            prompt = f'{prompt} [{default}]: '
        else:
            prompt = f'{prompt}: '
            
        while True:
            value = input(prompt).strip()
            if not value and default:
                return default
            elif value:
                return value
            print('This field is required.')

    def handle(self, *args, **options):
        # Try to get values from command line arguments first
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')
        interactive = options.get('interactive')
        
        # Try to get values from environment variables if not provided
        if not username:
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        if not email:
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        if not password:
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        # If still no values and interactive mode, prompt the user
        if interactive:
            if not username:
                username = self.get_input_data('username', 'Username')
            if not email:
                email = self.get_input_data('email', 'Email address')
            if not password:
                while True:
                    password = getpass.getpass('Password: ')
                    if password:
                        password_confirm = getpass.getpass('Password (again): ')
                        if password == password_confirm:
                            break
                        print('Error: Your passwords didn\'t match.')
                    else:
                        print('Error: This field cannot be blank.')
        
        # Final validation
        if not all([username, email, password]):
            raise CommandError(
                'You must provide username, email, and password either as arguments, '
                'environment variables, or through interactive input.'
            )
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User {username} already exists. Skipping creation.'))
            return
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists. Skipping creation.'))
            return
        
        # Create the superuser
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {username}'))
            self.stdout.write(self.style.SUCCESS(f'Email: {email}'))
            return user
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))
            raise CommandError('Superuser creation failed. See error above.')
