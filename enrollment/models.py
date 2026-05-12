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
    phone_2 = models.CharField(max_length=30, blank=True, help_text="Ikkinchi telefon raqami")
    email = models.EmailField(blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, help_text="Viloyat/Shahar")
    child_name = models.CharField(max_length=200, blank=True, help_text="Bolaning ismi")
    child_age = models.IntegerField(null=True, blank=True, help_text="Bolaning yoshi")
    children_count = models.IntegerField(default=1, help_text="Bolalar soni")
    interested_grade = models.ForeignKey(Grade, null=True, blank=True, on_delete=models.SET_NULL)
    discount_info = models.CharField(max_length=200, blank=True, help_text="Chegirma ma'lumoti")
    source = models.ForeignKey(LeadSource, null=True, blank=True, on_delete=models.SET_NULL)
    meta_lead_id = models.CharField(max_length=100, blank=True, null=True, help_text="Meta Lead ID (Facebook/Instagram)")
    meta_campaign_name = models.CharField(max_length=200, blank=True, help_text="Meta kampaniya nomi")
    meta_adset_name = models.CharField(max_length=200, blank=True, help_text="Meta reklama to'plami")
    meta_form_name = models.CharField(max_length=200, blank=True, help_text="Meta forma nomi")
    meta_campaign_id = models.CharField(max_length=100, blank=True)
    meta_adset_id = models.CharField(max_length=100, blank=True)
    meta_ad_id = models.CharField(max_length=100, blank=True)
    meta_form_id = models.CharField(max_length=100, blank=True)
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
        ('no_answer', 'Javob yo\'q'),
        ('busy', 'Zan'),
    ]
    RECORDING_CONSENT = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qilindi'),
        ('declined', 'Rad etildi'),
        ('not_asked', 'So\'ralmadi'),
    ]

    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name='calls')
    campaign = models.ForeignKey(CallCampaign, null=True, blank=True, on_delete=models.SET_NULL, related_name='calls')
    agent = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='agent_calls')
    caller_number = models.CharField(max_length=30, help_text="Qo'ng'iroq qilgan raqam")
    callee_number = models.CharField(max_length=30, help_text="Qabul qiluvchi raqam")
    direction = models.CharField(max_length=10, choices=CALL_DIRECTION)
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='ringing')
    
    # Twilio integration
    twilio_call_sid = models.CharField(max_length=100, blank=True, null=True, help_text="Twilio Call SID")
    twilio_conference_sid = models.CharField(max_length=100, blank=True, null=True)
    
    # Recording
    recording_url = models.URLField(blank=True, null=True, help_text="Yozib olingan audio URL")
    recording_sid = models.CharField(max_length=100, blank=True, null=True)
    recording_consent = models.CharField(max_length=20, choices=RECORDING_CONSENT, default='pending')
    recording_consent_timestamp = models.DateTimeField(null=True, blank=True)
    recording_file = models.FileField(upload_to='call_recordings/%Y/%m/', blank=True, null=True)
    recording_duration = models.IntegerField(null=True, blank=True, help_text="Yozuv davomiyligi (soniya)")
    
    # Call metrics
    duration_seconds = models.IntegerField(null=True, blank=True)
    wait_time_seconds = models.IntegerField(null=True, blank=True, help_text="Kutish vaqti")
    talk_time_seconds = models.IntegerField(null=True, blank=True, help_text="Gaplashish vaqti")
    
    # Notes and tags
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Vergul bilan ajratilgan teglar")
    disposition = models.CharField(max_length=100, blank=True, help_text="Qo'ng'iroq natijasi")
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Quality and monitoring
    quality_score = models.IntegerField(null=True, blank=True, help_text="1-5 ball")
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_calls')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False, help_text="Muammo belgisi")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['lead', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.get_direction_display()}: {self.caller_number} → {self.callee_number} ({self.get_status_display()})"
    
    @property
    def formatted_duration(self):
        if not self.duration_seconds:
            return "0:00"
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{minutes}:{seconds:02d}"


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
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('busy', 'Zan'),
        ('break', 'Tanaffus'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    extension = models.CharField(max_length=10, blank=True, help_text="Ichki raqam")
    phone_number = models.CharField(max_length=30, blank=True, help_text="Operator telefon raqami")
    twilio_worker_sid = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    is_available = models.BooleanField(default=True)
    max_concurrent_calls = models.IntegerField(default=1)
    total_calls_handled = models.IntegerField(default=0)
    last_call_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Agent: {self.user.username} ({self.get_status_display()})"


class LeadStatusHistory(models.Model):
    """Lead status o'zgarish tarixi."""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Lead Status Histories'

    def __str__(self):
        return f"{self.lead.full_name}: {self.old_status} → {self.new_status}"


class LeadComment(models.Model):
    """Lead uchun izohlar."""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.comment[:50]}"


class CallQueue(models.Model):
    """Qo'ng'iroqlar navbati - kiruvchi qo'ng'iroqlar uchun."""
    QUEUE_STATUS = [
        ('waiting', 'Kutmoqda'),
        ('assigned', 'Tayinlangan'),
        ('answered', 'Javob berildi'),
        ('abandoned', 'Tashlab ketildi'),
        ('timeout', 'Vaqt tugadi'),
    ]
    
    call = models.OneToOneField(CallRecord, on_delete=models.CASCADE, related_name='queue_entry')
    queue_name = models.CharField(max_length=100, default='default')
    status = models.CharField(max_length=20, choices=QUEUE_STATUS, default='waiting')
    priority = models.IntegerField(default=0, help_text="Yuqori raqam = yuqori ustuvorlik")
    position = models.IntegerField(default=0)
    wait_time_seconds = models.IntegerField(default=0)
    assigned_agent = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    entered_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', 'entered_at']
        indexes = [
            models.Index(fields=['status', '-priority', 'entered_at']),
        ]
    
    def __str__(self):
        return f"Queue: {self.call.caller_number} - {self.get_status_display()}"


class CallRouting(models.Model):
    """Qo'ng'iroqlarni yo'naltirish qoidalari."""
    ROUTING_STRATEGY = [
        ('round_robin', 'Round Robin'),
        ('least_busy', 'Eng kam yuklangan'),
        ('longest_idle', 'Eng uzoq bo\'sh'),
        ('skill_based', 'Malaka asosida'),
        ('priority', 'Ustuvorlik asosida'),
    ]
    
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=30, unique=True, help_text="Asosiy raqam")
    strategy = models.CharField(max_length=20, choices=ROUTING_STRATEGY, default='round_robin')
    is_active = models.BooleanField(default=True)
    business_hours_only = models.BooleanField(default=False)
    business_hours_start = models.TimeField(default='09:00')
    business_hours_end = models.TimeField(default='18:00')
    max_queue_size = models.IntegerField(default=50)
    max_wait_time_seconds = models.IntegerField(default=300)
    overflow_number = models.CharField(max_length=30, blank=True, help_text="Navbat to'lganda yo'naltirish")
    welcome_message = models.TextField(blank=True)
    queue_music_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class AuditLog(models.Model):
    """Tizim audit logi - barcha muhim harakatlar."""
    ACTION_TYPES = [
        ('call_initiated', 'Qo\'ng\'iroq boshlandi'),
        ('call_answered', 'Qo\'ng\'iroqga javob berildi'),
        ('call_ended', 'Qo\'ng\'iroq tugadi'),
        ('recording_started', 'Yozuv boshlandi'),
        ('recording_stopped', 'Yozuv to\'xtatildi'),
        ('recording_accessed', 'Yozuvga kirish'),
        ('recording_deleted', 'Yozuv o\'chirildi'),
        ('agent_status_changed', 'Agent holati o\'zgartirildi'),
        ('lead_created', 'Lead yaratildi'),
        ('lead_updated', 'Lead yangilandi'),
        ('settings_changed', 'Sozlamalar o\'zgartirildi'),
        ('user_login', 'Foydalanuvchi kirdi'),
        ('user_logout', 'Foydalanuvchi chiqdi'),
    ]
    
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    extra_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'}: {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class CallStatistics(models.Model):
    """Kunlik statistika - tezkor hisobotlar uchun."""
    date = models.DateField(unique=True)
    agent = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    total_calls = models.IntegerField(default=0)
    inbound_calls = models.IntegerField(default=0)
    outbound_calls = models.IntegerField(default=0)
    answered_calls = models.IntegerField(default=0)
    missed_calls = models.IntegerField(default=0)
    
    total_duration_seconds = models.IntegerField(default=0)
    total_talk_time_seconds = models.IntegerField(default=0)
    total_wait_time_seconds = models.IntegerField(default=0)
    
    avg_duration_seconds = models.FloatField(default=0)
    avg_wait_time_seconds = models.FloatField(default=0)
    
    recordings_count = models.IntegerField(default=0)
    recordings_with_consent = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['agent', '-date']),
        ]
    
    def __str__(self):
        agent_name = self.agent.username if self.agent else 'All Agents'
        return f"{agent_name} - {self.date}: {self.total_calls} calls"
