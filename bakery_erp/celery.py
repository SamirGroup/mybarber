"""
Celery configuration for background tasks.
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bakery_erp.settings')

try:
    from celery import Celery
    from celery.schedules import crontab

    app = Celery('bakery_erp')
    app.config_from_object('django.conf:settings', namespace='CELERY')
    app.autodiscover_tasks()

    # Periodic tasks
    app.conf.beat_schedule = {
        'update-daily-statistics': {
            'task': 'enrollment.tasks.update_daily_statistics',
            'schedule': crontab(hour=0, minute=5),
        },
        'cleanup-old-recordings': {
            'task': 'enrollment.tasks.cleanup_old_recordings',
            'schedule': crontab(hour=2, minute=0),
        },
        'check-abandoned-calls': {
            'task': 'enrollment.tasks.check_abandoned_calls',
            'schedule': crontab(minute='*/5'),
        },
    }

    @app.task(bind=True)
    def debug_task(self):
        print(f'Request: {self.request!r}')
except ImportError:
    app = None
