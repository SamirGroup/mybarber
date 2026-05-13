from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import LeadStatus


@receiver(post_migrate)
def create_default_statuses(sender, **kwargs):
    """App yaratilganda yoki migrate bo'lganda default statuslarni yaratish."""
    if sender.name != 'callcenter':
        return

    defaults = [
        {'name': 'Yangi Lead', 'code': 'new', 'color': '#1a73e8', 'sort_order': 1},
        {'name': 'Qo\'ng\'iroq qilinmadi', 'code': 'not_called', 'color': '#b91c1c', 'sort_order': 2},
        {'name': 'Qo\'ng\'iroq qilindi', 'code': 'called', 'color': '#15803d', 'sort_order': 3},
        {'name': 'Keyinroq qo\'ng\'iroq', 'code': 'callback', 'color': '#854d0e', 'sort_order': 4},
        {'name': 'Qabul qilindi', 'code': 'received', 'color': '#065f46', 'sort_order': 5},
        {'name': 'Javob yo\'q', 'code': 'no_answer', 'color': '#475569', 'sort_order': 6},
        {'name': 'Noto\'g\'ri raqam', 'code': 'wrong_number', 'color': '#9d174d', 'sort_order': 7},
        {'name': 'Bekor qilindi', 'code': 'cancelled', 'color': '#6b7280', 'sort_order': 8},
    ]

    for s in defaults:
        LeadStatus.objects.get_or_create(code=s['code'], defaults=s)