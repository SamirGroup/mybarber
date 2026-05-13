from django.apps import AppConfig


class CallcenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'callcenter'
    verbose_name = 'Call Center CRM'

    def ready(self):
        import callcenter.signals  # noqa
