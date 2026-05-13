from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_callback_reminders():
    """Callback vaqti yetgan leadlar uchun eslatma yuborish"""
    from .models import Callback, Notification
    now = timezone.now()
    due_callbacks = Callback.objects.filter(
        is_done=False,
        callback_datetime__lte=now,
        callback_datetime__gte=now - timedelta(hours=1)
    ).select_related('lead', 'lead__assigned_operator')

    for cb in due_callbacks:
        lead = cb.lead
        if lead.assigned_operator:
            Notification.objects.get_or_create(
                user=lead.assigned_operator,
                lead=lead,
                notification_type='callback_due',
                is_read=False,
                defaults={
                    'notification_text': f"Callback vaqti keldi: {lead.full_name} ({lead.phone_number})"
                }
            )
        for admin in User.objects.filter(is_superuser=True):
            Notification.objects.get_or_create(
                user=admin,
                lead=lead,
                notification_type='callback_due',
                is_read=False,
                defaults={
                    'notification_text': f"Callback: {lead.full_name} — operator: {lead.assigned_operator}"
                }
            )
    logger.info(f"Callback reminders sent: {due_callbacks.count()}")


@shared_task
def send_not_called_reminders():
    """Ertasi kuni soat 09:00 da 'Qo'ngiroq qilinmadi' statusli leadlar uchun eslatma"""
    from .models import MetaLead, Notification, LeadStatus
    status = LeadStatus.objects.filter(code='not_called').first()
    if not status:
        return

    leads = MetaLead.objects.filter(
        current_status=status,
        is_closed=False
    ).select_related('assigned_operator')

    for lead in leads:
        if lead.assigned_operator:
            Notification.objects.create(
                user=lead.assigned_operator,
                lead=lead,
                notification_text=f"Eslatma: {lead.full_name} ga hali qo'ngiroq qilinmadi!",
                notification_type='reminder'
            )
    logger.info(f"Not-called reminders sent: {leads.count()}")


@shared_task
def alert_untouched_leads():
    """24 soat davomida tegib ko'rilmagan leadlar haqida admin alert"""
    from .models import MetaLead, Notification
    threshold = timezone.now() - timedelta(hours=24)
    untouched = MetaLead.objects.filter(
        crm_received_time__lte=threshold,
        is_closed=False,
        history__isnull=True
    ).distinct()

    for lead in untouched:
        for admin in User.objects.filter(is_superuser=True):
            Notification.objects.get_or_create(
                user=admin,
                lead=lead,
                notification_type='untouched',
                is_read=False,
                defaults={
                    'notification_text': f"24 soat o'tdi, lead tegib ko'rilmadi: {lead.full_name}"
                }
            )
    logger.info(f"Untouched lead alerts: {untouched.count()}")
