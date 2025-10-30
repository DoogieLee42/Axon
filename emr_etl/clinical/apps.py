from django.apps import AppConfig

class ClinicalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinical'

    def ready(self):
        # signals 등록
        from . import signals  # noqa: F401
