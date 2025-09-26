from django.apps import AppConfig


class AiServicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_services"

    def ready(self):
        # Import assistant registry to ensure assistants are registered at startup
        try:
            from . import ai_assistants  # noqa: F401
        except ImportError:
            pass