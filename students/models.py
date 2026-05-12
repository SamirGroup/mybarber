from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from enrollment.models import Grade, AcademicYear


class Classroom(models.Model):
    name = models.CharField(max_length=100)  # e.g. "5-A"
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name='classrooms')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='classrooms')
    homeroom_teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='homeroom_classes')
    capacity = models.IntegerField(default=30)

    class Meta:
        ordering = ['grade__sort_order', 'name']
        unique_together = ['name', 'academic_year']

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class Parent(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    phone2 = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    relation = models.CharField(max_length=50, default='Ota')  # Ota, Ona, Vasiy

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.phone})"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}"


class Student(models.Model):
    GENDER_CHOICES = [('M', "O'g'il"), ('F', 'Qiz')]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birth_date = models.DateField()
    passport_or_id = models.CharField(max_length=50, blank=True, help_text="Metrika yoki ID karta raqami")
    erp_number = models.CharField(max_length=50, blank=True, help_text="ERP maktab tizimidagi raqam")
    photo = models.ImageField(upload_to='students/photos/', null=True, blank=True)
    classroom = models.ForeignKey(Classroom, null=True, blank=True, on_delete=models.SET_NULL, related_name='students')
    parents = models.ManyToManyField(Parent, blank=True, related_name='children')
    address = models.TextField(blank=True)
    medical_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    enrolled_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    @property
    def age(self):
        today = timezone.now().date()
        b = self.birth_date
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


# ── Documents ─────────────────────────────────────────────────────────
class DocumentType(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Ma'lumotnoma, Tabel, Pasport nusxasi...
    is_required = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class StudentDocument(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    title = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='students/documents/')
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} — {self.doc_type}"


# ── Schedule / Subjects ───────────────────────────────────────────────
class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name


class Schedule(models.Model):
    DAYS = [
        (1, 'Dushanba'), (2, 'Seshanba'), (3, 'Chorshanba'),
        (4, 'Payshanba'), (5, 'Juma'), (6, 'Shanba'),
    ]
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='teaching_schedules')
    day_of_week = models.IntegerField(choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.classroom} | {self.get_day_of_week_display()} {self.start_time} — {self.subject}"


# ── Grades (Baholar) ──────────────────────────────────────────────────
class Quarter(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='quarters')
    number = models.IntegerField()  # 1,2,3,4
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ['academic_year', 'number']
        unique_together = ['academic_year', 'number']

    def __str__(self):
        return f"{self.academic_year} — {self.number}-chorak"


class DailyGrade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='daily_grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    date = models.DateField(default=timezone.now)
    grade = models.DecimalField(max_digits=4, decimal_places=1)
    comment = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} | {self.subject} | {self.date} — {self.grade}"


class QuarterGrade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quarter_grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE)
    grade = models.DecimalField(max_digits=4, decimal_places=1)
    teacher = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ['student', 'subject', 'quarter']

    def __str__(self):
        return f"{self.student} | {self.subject} | {self.quarter} — {self.grade}"


# ── Attendance ────────────────────────────────────────────────────────
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Keldi'),
        ('absent', 'Kelmadi'),
        ('late', 'Kech keldi'),
        ('excused', 'Uzrli'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    marked_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['student', 'date', 'subject']

    def __str__(self):
        return f"{self.student} | {self.date} — {self.get_status_display()}"


# ── Homework ──────────────────────────────────────────────────────────
class Homework(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='homeworks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='students/homework/', null=True, blank=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.classroom} | {self.subject} — {self.title}"


# ── Finance ───────────────────────────────────────────────────────────
class Contract(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='contracts')
    contract_number = models.CharField(max_length=100, unique=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    monthly_fee = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_reason = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract_number} — {self.student}"

    @property
    def effective_fee(self):
        return self.monthly_fee * (1 - self.discount_percent / 100)


class Payment(models.Model):
    PAYMENT_METHOD = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('transfer', "O'tkazma"),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    contract = models.ForeignKey(Contract, null=True, blank=True, on_delete=models.SET_NULL, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='cash')
    payment_date = models.DateField(default=timezone.now)
    month_for = models.DateField(help_text="Qaysi oy uchun to'lov")
    received_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.student} | {self.month_for} — {self.amount}"


# ── SMS Notification ──────────────────────────────────────────────────
class SmsNotificationConfig(models.Model):
    """Har oyning qaysi kunida qarzdor ota-onalarga SMS jo'natilsin."""
    day_of_month = models.IntegerField(default=5, help_text="Har oyning necha-sida SMS jo'natilsin (1-28)")
    is_active = models.BooleanField(default=True)
    message_template = models.TextField(
        default="Hurmatli {parent_name}! Farzandingiz {student_name} uchun {contract_number} shartnoma bo'yicha {debt_amount} so'm qarzdorlik mavjud. Iltimos, to'lovni amalga oshiring."
    )

    class Meta:
        verbose_name = "SMS sozlamasi"

    def __str__(self):
        return f"SMS — har oyning {self.day_of_month}-kuni"


class SmsLog(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='sms_logs')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sms_logs')
    contract = models.ForeignKey(Contract, null=True, blank=True, on_delete=models.SET_NULL)
    phone = models.CharField(max_length=30)
    message = models.TextField()
    debt_amount = models.DecimalField(max_digits=12, decimal_places=2)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    error = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.parent} → {self.phone} | {self.sent_at.date()}"


# ── Internal Chat ─────────────────────────────────────────────────────
class ChatGroup(models.Model):
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_chats')
    classroom = models.ForeignKey(Classroom, null=True, blank=True, on_delete=models.SET_NULL, related_name='chat_groups')
    students = models.ManyToManyField(Student, blank=True, related_name='chat_groups')
    members = models.ManyToManyField(User, blank=True, related_name='chat_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ChatMessage(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    file = models.FileField(upload_to='students/chat/', null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read_by_admin = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"{self.sender} → {self.group} | {self.sent_at:%Y-%m-%d %H:%M}"
