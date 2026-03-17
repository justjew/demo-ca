from django.apps import AppConfig


class DjangoOrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"  # type: ignore
    name = "adapters.db.django_orm"
    label = "django_orm"
