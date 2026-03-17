from django.apps import AppConfig


class DrfApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"  # type: ignore
    name = "adapters.web.drf_api"
    label = "drf_api"
