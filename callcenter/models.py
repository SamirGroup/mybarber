from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class LeadStatus(models.Model):
    STATUS_CHOICES = [
        ('new', 'Yangi Lead'),
        ('not_called', 'Qo\'ngiroq qilinmadi'),
        ('called', 'Qo\'ngiroq qilindi'),
        ('callback', 'Keyinroq qo\'ngiroq'),
        ('received', 'Qabul qilindi'),
        ('no_answer', 'Javob bermadi'),
        ('wrong_number', 'Noto\'g\'ri raqam'),
        ('cancelled', 'Bekor qilindi'),
    ]
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=30, unique=True)
    color = models.CharField(max_length=20, default='secondary')
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class MetaLead(models.Model):
    lead_uuid = models.CharField(max_length=100, unique=True, blank=True)
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=30)
    phone_number2 = models.CharField(max_length=30, blank=True)
    region = models.CharField(max_length=100, blank=True)
    product_interest = models.CharField(max_length=200, blank=True)
    campaign_name = models.CharField(max_length=200, blank=True)
    adset_name = models.CharField(max_length=200, blank=True)
    form_name = models.CharField(max_length=200, blank=True)
    meta_created_time = models.DateTimeField(null=True, blank=True)
    crm_received_time = models.DateTimeField(default=timezone.now)
    assigned_operator = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='cc_assigned_leads'
    )
    current_status = models.ForeignKey(
        LeadStatus, null=True, blank=True, on_delete=models.SET_NULL, related_name='leads'
    )
    callback_date = models.DateTimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    raw_payload = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-crm_received_time']

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


class LeadStatusHistory(models.Model):
    lead = models.ForeignKey(MetaLead, on_delete=models.CASCADE, related_name='history')
    old_status = models.ForeignKey(
        LeadStatus, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    new_status = models.ForeignKey(
        LeadStatus, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    operator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='cc_status_history')
    comment = models.TextField(blank=True)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-changed_at']


class LeadComment(models.Model):
    lead = models.ForeignKey(MetaLead, on_delete=models.CASCADE, related_name='comments')
    operator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='cc_comments')
    comment_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']


class Callback(models.Model):
    lead = models.ForeignKey(MetaLead, on_delete=models.CASCADE, related_name='callbacks')
    callback_datetime = models.DateTimeField()
    callback_note = models.TextField(blank=True)
    is_done = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['callback_datetime']

    def __str__(self):
        return f"{self.lead} — {self.callback_datetime}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('new_lead', 'Yangi lead'),
        ('callback_due', 'Callback vaqti'),
        ('untouched', 'Tegib ko\'rilmagan'),
        ('reminder', 'Eslatma'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cc_notifications')
    lead = models.ForeignKey(MetaLead, null=True, blank=True, on_delete=models.SET_NULL)
    notification_text = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='reminder')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']


class ApiLog(models.Model):
    api_name = models.CharField(max_length=100)
    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    status_code = models.IntegerField(default=200)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']


class ReportLog(models.Model):
    report_type = models.CharField(max_length=100)
    generated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-generated_at']


class SystemSettings(models.Model):
    ASSIGN_MODE_CHOICES = [
        ('round_robin', 'Round Robin (avtomatik)'),
        ('manual', 'Qo\'lda (admin tomonidan)'),
    ]
    assign_mode = models.CharField(max_length=20, choices=ASSIGN_MODE_CHOICES, default='round_robin')
    round_robin_index = models.IntegerField(default=0)
    meta_verify_token = models.CharField(max_length=200, blank=True)
    meta_access_token = models.CharField(max_length=500, blank=True)
    meta_app_secret = models.CharField(max_length=200, blank=True)
    meta_page_id = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'System Settings'

    def __str__(self):
        return 'System Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
