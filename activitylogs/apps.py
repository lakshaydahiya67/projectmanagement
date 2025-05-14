from django.apps import AppConfig


class ActivitylogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activitylogs'
    verbose_name = 'Activity Logs'
    
    def ready(self):
        """Connect signals when the app is ready"""
        # Import signals here to avoid circular imports
        import activitylogs.signals 