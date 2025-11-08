from django.apps import AppConfig


class MvpUiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mvp_ui'
    verbose_name = 'MVP UI & API Coverage'
    
    def ready(self):
        """Initialize performance tracking on app ready"""
        from .middleware import PerformanceTracker
        # Singleton instance for tracking
        PerformanceTracker.get_instance()
