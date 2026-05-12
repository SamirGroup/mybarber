from django.apps import AppConfig


class EnrollmentConfig(AppConfig):
    name = "enrollment"
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import enrollment.signals
