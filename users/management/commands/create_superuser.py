from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser with the specified email and password'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Superuser username')
        parser.add_argument('--email', type=str, help='Superuser email')
        parser.add_argument('--password', type=str, help='Superuser password')
        parser.add_argument('--noinput', action='store_false', dest='interactive',
                          help='Tells Django to NOT prompt the user for input of any kind.')

    def handle(self, *args, **options):
        username = options.get('username') or settings.DJANGO_SUPERUSER_USERNAME
        email = options.get('email') or settings.DJANGO_SUPERUSER_EMAIL
        password = options.get('password') or settings.DJANGO_SUPERUSER_PASSWORD
        interactive = options.get('interactive')

        if not all([username, email]) and not password:
            raise CommandError('You must provide both username/email and password or set them in settings')

        if interactive:
            confirm = input(f"""You have requested to create a superuser with username '{username}' and email '{email}'. 
Are you sure you want to continue? (y/n): """)
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Superuser creation cancelled.'))
                return

        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.WARNING(f'User {username} already exists. Skipping creation.'))
            return
        except User.DoesNotExist:
            pass

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
            raise CommandError(f'Error creating superuser: {str(e)}')
