from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'
    verbose_name = 'Analytics'
    
    def ready(self):
        """Connect signals when the app is ready"""
        # Import signals here to avoid circular imports
        import analytics.signals
