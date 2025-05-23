from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizations'
    
    def ready(self):
        """Import signals when app is ready"""
        import organizations.signals  # noqa