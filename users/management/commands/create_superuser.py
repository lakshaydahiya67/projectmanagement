import os
import getpass
import sys
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser with the specified email and password'
    requires_migrations_checks = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(self.UserModel.USERNAME_FIELD)

    def add_arguments(self, parser):
        parser.add_argument(
            '--%s' % self.UserModel.USERNAME_FIELD,
            dest='username',
            default=None,
            help='Specifies the username for the superuser.',
        )
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false',
            dest='interactive',
            help=(
                'Tells Django to NOT prompt the user for input of any kind. '
                'You must use --username with --noinput, along with an option for '
                'any other required field.'
            ),
        )
        parser.add_argument(
            '--database',
            default='default',
            help='Specifies the database to use. Default is "default".',
        )

    def get_input_data(self, field, message, default=None):
        """Get input data from user or use default if provided."""
        raw_value = None
        input_msg = message
        if default:
            input_msg += f' [{default}]'
        input_msg += ': '

        while raw_value is None:
            raw_value = input(input_msg).strip()
            if not raw_value and default:
                raw_value = default
            elif not raw_value:
                self.stderr.write("Error: This field cannot be blank.")
                raw_value = None
                continue
            
            try:
                val = field.clean(raw_value, None)
                return val
            except Exception as e:
                self.stderr.write(f"Error: {e}")
                raw_value = None

    def handle(self, *args, **options):
        username = options.get('username')
        database = options.get('database')
        interactive = options.get('interactive')

        # Get values from environment variables if not provided
        if not username:
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        # Validate that the username is provided in non-interactive mode
        if not interactive and not username:
            raise CommandError(
                'You must use --username with --noinput.'
            )

        # Interactive mode: Prompt for missing credentials
        if interactive:
            default_username = username or ''
            default_email = email or ''
            
            try:
                # Validate that the username is valid
                if not username:
                    username = self.get_input_data(
                        self.username_field, 
                        'Username',
                        default_username,
                    )
                
                # Get email if not provided
                if not email:
                    email = self.get_input_data(
                        self.UserModel._meta.get_field('email'),
                        'Email address',
                        default_email,
                    )
                
                # Get password if not provided
                if not password:
                    while True:
                        password = getpass.getpass('Password: ')
                        if not password:
                            self.stderr.write("Error: This field cannot be blank.")
                            continue
                        password2 = getpass.getpass('Password (again): ')
                        if password != password2:
                            self.stderr.write("Error: Your passwords didn't match.")
                            continue
                        break
            except KeyboardInterrupt:
                self.stderr.write("\nOperation cancelled.")
                sys.exit(1)
        
        # Final validation
        if not all([username, password]):
            raise CommandError(
                'You must provide username and password either as arguments, '
                'environment variables, or through interactive input.'
            )

        # Check if user already exists
        if self.UserModel._default_manager.db_manager(database).filter(
            **{self.UserModel.USERNAME_FIELD: username}
        ).exists():
            self.stdout.write(
                self.style.WARNING(f'User {username} already exists. Skipping creation.')
            )
            return
        
        # Create the superuser
        try:
            with transaction.atomic(using=database):
                user = self.UserModel._default_manager.db_manager(database).create_superuser(
                    **{
                        self.UserModel.USERNAME_FIELD: username,
                        'email': email,
                        'password': password,
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created superuser: {username}')
                )
                if email:
                    self.stdout.write(
                        self.style.SUCCESS(f'Email: {email}')
                    )
                return user
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )
            if hasattr(e, '__cause__') and e.__cause__:
                self.stderr.write(f"Caused by: {e.__cause__}")
            raise CommandError('Superuser creation failed. See error above.')
        finally:
            # Clear sensitive data
            del password
