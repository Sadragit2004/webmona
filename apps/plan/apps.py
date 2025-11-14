from django.apps import AppConfig


class PlanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.plan'

    def ready(self):
        import apps.plan.signals