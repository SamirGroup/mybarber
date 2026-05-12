from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class LeadSource(models.Model):
    """Lead qayerdan kelgani: Meta, veb-sayt, qo'ng'iroq, tavsiya va h.k."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=30, unique=True, help_text="e.g., meta, web, phone, referral")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Grade(models.Model):
    """Sinf darajalari (Grade 1, Grade 2, ..., Grade 12)"""
    name = models.CharField(max_length=50, unique=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    """O'quv yili (2025-2026, 2026-2027...)"""
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Lead(models.Model):
    """Meta Lead yordamida yoki qo'lda yaratilgan potensial ota-ona so'rovlari."""

    LEAD_STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('contacted', 'Bog\'lanildi'),
        ('interested', 'Qiziqish bor'),
        ('appointment', 'Uchrashuv belgilangan'),
        ('registered', 'Ro\'yxatdan o\'tdi'),
        ('declined', 'Rad etildi'),
        ('not_reachable', 'Bog\'lanib bo\'lmadi'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True, null=True)
    child_name = models.CharField(max_length=200, blank=True, help_text="Bolaning ismi")
    child_age = models.IntegerField(null=True, blank=True, help_text="Bolaning yoshi")
    interested_grade = models.ForeignKey(Grade, null=True, blank=True, on_delete=models.SET_NULL)
    source = models.ForeignKey(LeadSource, null=True, blank=True, on_delete=models.SET_NULL)
    meta_lead_id = models.CharField(max_length=100, blank=True, null=True, help_text="Meta Lead ID (Facebook/Instagram)")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_leads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contacted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.phone} ({self.get_status_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class CallCampaign(models.Model):
    """Qo'ng'iroq kampaniyasi — guruhlab qo'ng'iroq qilish uchun."""

    CAMPAIGN_STATUS = [
        ('draft', 'Qoralama'),
        ('active', 'Faol'),
        ('completed', 'Yakunlandi'),
        ('paused', 'To\'xtatildi'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='draft')
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class CallRecord(models.Model):
    """Har bir telefon qo'ng'irog'ining yozuvi."""

    CALL_DIRECTION = [
        ('inbound', 'Kiruvchi'),
        ('outbound', 'Chiquvchi'),
    ]
    CALL_STATUS = [
        ('ringing', 'Qo\'ng\'iroq qilinmoqda'),
        ('in_progress', 'Gaplashmoqda'),
        ('completed', 'Yakunlandi'),
        ('missed', 'Javob berilmadi'),
        ('voicemail', 'Ovozli xabar'),
        ('failed', 'Muvaffaqiyatsiz'),
    ]

    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name='calls')
    campaign = models.ForeignKey(CallCampaign, null=True, blank=True, on_delete=models.SET_NULL, related_name='calls')
    agent = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='agent_calls')
    caller_number = models.CharField(max_length=30, help_text="Qo'ng'iroq qilgan raqam")
    callee_number = models.CharField(max_length=30, help_text="Qabul qiluvchi raqam")
    direction = models.CharField(max_length=10, choices=CALL_DIRECTION)
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='ringing')
    twilio_call_sid = models.CharField(max_length=100, blank=True, null=True, help_text="Twilio Call SID")
    recording_url = models.URLField(blank=True, null=True, help_text="Yozib olingan audio URL")
    recording_sid = models.CharField(max_length=100, blank=True, null=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_direction_display()}: {self.caller_number} → {self.callee_number} ({self.get_status_display()})"


class StudentApplication(models.Model):
    """O'quvchi qabul qilish uchun to'liq ariza."""

    APPLICATION_STATUS = [
        ('draft', 'Qoralama'),
        ('submitted', 'Topshirildi'),
        ('under_review', 'Ko\'rib chiqilmoqda'),
        ('documents_pending', 'Hujjatlar kutilmoqda'),
        ('assessment', 'Sinov'),
        ('approved', 'Qabul qilindi'),
        ('enrolled', 'Ro\'yxatdan o\'tdi'),
        ('rejected', 'Rad etildi'),
        ('waitlisted', 'Kutish ro\'yxati'),
    ]
    GENDER_CHOICES = [
        ('M', 'O\'g\'il'),
        ('F', 'Qiz'),
    ]

    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name='applications')
    # Ota-ona ma'lumotlari
    parent_first_name = models.CharField(max_length=100)
    parent_last_name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=30)
    parent_email = models.EmailField(blank=True, null=True)
    parent_relation = models.CharField(max_length=50, default='Ota', help_text="Ota, Ona, Vasiy...")
    # Bola ma'lumotlari
    student_first_name = models.CharField(max_length=100)
    student_last_name = models.CharField(max_length=100)
    student_dob = models.DateField(help_text="Tug'ilgan sana")
    student_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    applying_grade = models.ForeignKey(Grade, null=True, blank=True, on_delete=models.SET_NULL)
    previous_school = models.CharField(max_length=200, blank=True)
    medical_notes = models.TextField(blank=True, help_text="Tibbiy eslatmalar")
    # Ariza holati
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='draft')
    application_fee_paid = models.BooleanField(default=False)
    application_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_applications')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student_first_name} {self.student_last_name} — {self.applying_grade or 'N/A'} ({self.get_status_display()})"

    @property
    def parent_full_name(self):
        return f"{self.parent_first_name} {self.parent_last_name}".strip()

    @property
    def student_full_name(self):
        return f"{self.student_first_name} {self.student_last_name}".strip()


class AgentProfile(models.Model):
    """Call centre agentining qo'shimcha profili."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    extension = models.CharField(max_length=10, blank=True, help_text="Ichki raqam")
    twilio_worker_sid = models.CharField(max_length=100, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    max_concurrent_calls = models.IntegerField(default=1)

    def __str__(self):
        return f"Agent: {self.user.username} (ext: {self.extension or 'N/A'})"
