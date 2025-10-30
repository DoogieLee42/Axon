from django.apps import AppConfig


class MasterdataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "emr_etl.masterdata"
    verbose_name = "ETL · Masterdata Integration"
