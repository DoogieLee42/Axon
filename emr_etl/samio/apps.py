from django.apps import AppConfig


class SamioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "emr_etl.samio"
    verbose_name = "ETL · SAM Export"
