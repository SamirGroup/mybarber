"""
Celery configuration for background tasks.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bakery_erp.settings')

app = Celery('bakery_erp')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'update-daily-statistics': {
        'task': 'enrollment.tasks.update_daily_statistics',
        'schedule': crontab(hour=0, minute=5),  # Har kuni 00:05 da
    },
    'cleanup-old-recordings': {
        'task': 'enrollment.tasks.cleanup_old_recordings',
        'schedule': crontab(hour=2, minute=0),  # Har kuni 02:00 da
    },
    'check-abandoned-calls': {
        'task': 'enrollment.tasks.check_abandoned_calls',
        'schedule': crontab(minute='*/5'),  # Har 5 daqiqada
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
