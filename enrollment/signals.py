from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Lead, LeadStatusHistory


@receiver(pre_save, sender=Lead)
def track_lead_status_change(sender, instance, **kwargs):
    """Lead status o'zgarganda tarixga yozish."""
    if instance.pk:
        try:
            old_lead = Lead.objects.get(pk=instance.pk)
            if old_lead.status != instance.status:
                instance._old_status = old_lead.status
                instance._status_changed = True
            else:
                instance._status_changed = False
        except Lead.DoesNotExist:
            instance._status_changed = False
    else:
        instance._status_changed = True
        instance._old_status = ''


@receiver(post_save, sender=Lead)
def create_status_history(sender, instance, created, **kwargs):
    """Status o'zgarganda tarix yaratish."""
    if hasattr(instance, '_status_changed') and instance._status_changed:
        LeadStatusHistory.objects.create(
            lead=instance,
            old_status=getattr(instance, '_old_status', ''),
            new_status=instance.status,
            changed_by=getattr(instance, '_changed_by', None),
        )
