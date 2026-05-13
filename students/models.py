from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum
from enrollment.models import Grade, AcademicYear
from datetime import timedelta


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

    @property
    def total_discount(self):
        """Barcha aktiv shartnomalardagi chegirmalar"""
        total = 0
        for contract in self.contracts.filter(is_active=True):
            total += contract.discount_percent
        return total
    
    @property
    def has_discount(self):
        """Chegirmasi bormi"""
        return self.contracts.filter(is_active=True, discount_percent__gt=0).exists()
    
    def get_discount_details(self):
        """Chegirma ma'lumotlari"""
        discounts = []
        for contract in self.contracts.filter(is_active=True, discount_percent__gt=0):
            discounts.append({
                'contract_number': contract.contract_number,
                'discount_percent': contract.discount_percent,
                'discount_reason': contract.discount_reason,
                'effective_fee': contract.effective_fee,
            })
        return discounts
    
    def get_balance_for_month(self, year, month):
        """Belgilangan oy uchun to'lov va qarzdorlik"""
        total_debt = 0
        total_paid = 0
        
        for contract in self.contracts.filter(is_active=True):
            paid = contract.payments.filter(
                payment_date__year=year,
                payment_date__month=month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Oy uchun kutilayotgan to'lov
            expected = contract.effective_fee
            
            total_paid += paid
            total_debt += max(0, expected - paid)
        
        return {
            'total_debt': total_debt,
            'total_paid': total_paid,
            'expected': total_paid + total_debt,
        }
    
    def get_quarter_grades_by_subject(self, quarter):
        """Belgilangan chorak bo'yicha fanlar bo'yicha baholar"""
        grades = self.quarter_grades.filter(quarter=quarter).select_related('subject')
        result = {}
        for grade in grades:
            result[grade.subject.name] = float(grade.grade)
        return result
    
    def get_average_grade(self):
        """O'rtacha baho"""
        from django.db.models import Avg
        avg = self.quarter_grades.aggregate(avg=Avg('grade'))['avg']
        return round(avg, 2) if avg else 0
    
    def get_attendance_rate(self, start_date=None, end_date=None):
        """Davomat foizi"""
        from django.db.models import Count, Q
        
        if start_date is None:
            start_date = timezone.now().date() - timedelta(days=30)
        if end_date is None:
            end_date = timezone.now().date()
        
        total = self.attendances.filter(date__range=[start_date, end_date]).count()
        present = self.attendances.filter(
            date__range=[start_date, end_date],
            status='present'
        ).count()
        late = self.attendances.filter(
            date__range=[start_date, end_date],
            status='late'
        ).count()
        
        if total == 0:
            return 0
        
        return round(((present + late * 0.5) / total) * 100, 2)


# ── Documents ─────────────────────────────────────────────────────────
class DocumentType(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Ma'lumotnoma, Tabel, Pasport nusxasi...
    is_required = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class DocumentTemplate(models.Model):
    """Hujjatlar generatsiyasi uchun shablonlar"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True, help_text="Masalan: student_card, certificate")
    template_text = models.TextField(help_text="O'zgaruvchilar: {{student_name}}, {{classroom}}, {{date}}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def generate(self, context):
        """Hujjat generatsiya qilish"""
        text = self.template_text
        for key, value in context.items():
            text = text.replace('{{' + key + '}}', str(value))
        return text


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


class LessonPeriod(models.Model):
    """Dars soatlari — kichik va katta sinflar uchun alohida"""
    LEVEL_CHOICES = [
        ('primary', 'Boshlang\'ich (1-4 sinf)'),
        ('secondary', 'O\'rta (5-9 sinf)'),
        ('high', 'Yuqori (10-11 sinf)'),
    ]
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    lesson_number = models.IntegerField(help_text='1-soat, 2-soat...')
    start_time = models.TimeField()
    end_time = models.TimeField()
    label = models.CharField(max_length=50, blank=True, help_text='Masalan: 1-dars, Tanaffus')

    class Meta:
        ordering = ['level', 'lesson_number']
        unique_together = ['level', 'lesson_number']

    def __str__(self):
        return f"{self.get_level_display()} | {self.lesson_number}-soat ({self.start_time:%H:%M}–{self.end_time:%H:%M})"


class Schedule(models.Model):
    DAYS = [
        (1, 'Dushanba'), (2, 'Seshanba'), (3, 'Chorshanba'),
        (4, 'Payshanba'), (5, 'Juma'), (6, 'Shanba'),
    ]
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='teaching_schedules')
    day_of_week = models.IntegerField(choices=DAYS)
    period = models.ForeignKey(LessonPeriod, null=True, blank=True, on_delete=models.SET_NULL, related_name='schedules')
    # Eski maydonlar — period bo'lmasa fallback
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    room = models.CharField(max_length=50, blank=True, help_text='Xona raqami')

    class Meta:
        ordering = ['day_of_week', 'period__lesson_number', 'start_time']

    def __str__(self):
        period_str = f"{self.period.lesson_number}-soat" if self.period else str(self.start_time)
        return f"{self.classroom} | {self.get_day_of_week_display()} {period_str} — {self.subject}"

    @property
    def effective_start(self):
        return self.period.start_time if self.period else self.start_time

    @property
    def effective_end(self):
        return self.period.end_time if self.period else self.end_time


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
    
    # Qo'shimcha: Kimlarga biriktirilgan (butun sinf yoki alohida o'quvchilar)
    students = models.ManyToManyField(Student, blank=True, related_name='assigned_homeworks', 
                                       help_text="Bo'sh qoldirilsa, butun sinfga biriktiriladi")

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.classroom} | {self.subject} — {self.title}"


class HomeworkSubmission(models.Model):
    """O'quvchi tomonidan topshirilgan uy vazifasi"""
    STATUS_CHOICES = [
        ('submitted', 'Topshirildi'),
        ('graded', 'Baholandi'),
        ('returned', 'Qaytarildi'),
    ]
    
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homework_submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField(blank=True)
    file = models.FileField(upload_to='students/homework_submissions/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    grade = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    teacher_comment = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['homework', 'student']
    
    def __str__(self):
        return f"{self.student} | {self.homework} | {self.status}"


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

    def get_total_paid(self):
        """Jami to'langan summa"""
        return self.payments.aggregate(total=Sum('amount'))['total'] or 0

    def get_balance(self):
        """Joriy qarzdorlik"""
        today = timezone.now().date()
        months_active = self._months_between(self.start_date, today)
        expected = self.effective_fee * months_active
        paid = self.get_total_paid()
        return max(0, expected - paid)
    
    def _months_between(self, start, end):
        """Ikkita sana orasidagi oylar soni"""
        return (end.year - start.year) * 12 + (end.month - start.month) + 1
    
    def get_payment_history(self):
        """To'lovlar tarixi"""
        return self.payments.select_related('received_by').order_by('-payment_date')


class StudentBalance(models.Model):
    """O'quvchi qarzdorligini avtomatik hisoblash"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='balance')
    total_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} — Qarz: {self.total_debt} so'm"

    def update_balance(self):
        """Qarzdorlikni qayta hisoblash"""
        today = timezone.now().date()
        total = 0
        
        for contract in self.student.contracts.filter(is_active=True):
            months_active = self._months_between(contract.start_date, today)
            expected = contract.effective_fee * months_active
            paid = contract.payments.aggregate(s=Sum('amount'))['s'] or 0
            total += max(0, expected - paid)
        
        self.total_debt = total
        self.save()
        return total
    
    def _months_between(self, start, end):
        """Ikkita sana orasidagi oylar soni"""
        return (end.year - start.year) * 12 + (end.month - start.month) + 1


class MonthlyPayment(models.Model):
    """Har oy uchun avtomatik yaratiladigan to'lov"""
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('paid', 'To\'langan'),
        ('partial', 'Qisman to\'langan'),
        ('overdue', 'Muddati o\'tgan'),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='monthly_payments')
    month = models.DateField(help_text="Qaysi oy uchun (YYYY-MM-01)")
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField(help_text="To'lov muddati")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month']
        unique_together = ['contract', 'month']
    
    def __str__(self):
        return f"{self.contract.student} | {self.month:%Y-%m} — {self.amount_due} so'm"
    
    def update_status(self):
        """Statusni yangilash"""
        today = timezone.now().date()
        
        if self.amount_paid >= self.amount_due:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        elif today > self.due_date:
            self.status = 'overdue'
        else:
            self.status = 'pending'
        
        self.save()


class Payment(models.Model):
    PAYMENT_METHOD = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('transfer', "O'tkazma"),
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('uzum', 'Uzum Bank'),
        ('apelsin', 'Apelsin'),
        ('humo', 'Humo'),
        ('uzcard', 'UzCard'),
        ('online', 'Online to\'lov'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    contract = models.ForeignKey(Contract, null=True, blank=True, on_delete=models.SET_NULL, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='cash')
    payment_date = models.DateField(default=timezone.now)
    month_for = models.DateField(help_text="Qaysi oy uchun to'lov")
    received_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=200, blank=True)
    # Online to'lov ma'lumotlari
    transaction_id = models.CharField(max_length=200, blank=True, help_text='Online to\'lov tranzaksiya ID')
    is_confirmed = models.BooleanField(default=True, help_text='Online to\'lovlar uchun tasdiqlash holati')
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
    GROUP_TYPE_CHOICES = [
        ('classroom', 'Sinf guruhi'),
        ('subject', 'Fan guruhi'),
        ('custom', 'Maxsus guruh'),
    ]
    
    name = models.CharField(max_length=200)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPE_CHOICES, default='custom')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_chats')
    classroom = models.ForeignKey(Classroom, null=True, blank=True, on_delete=models.SET_NULL, related_name='chat_groups')
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL, related_name='chat_groups')
    students = models.ManyToManyField(Student, blank=True, related_name='chat_groups')
    members = models.ManyToManyField(User, blank=True, related_name='chat_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ChatMessage(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    file = models.FileField(upload_to='students/chat/', null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"{self.sender} → {self.group} | {self.sent_at:%Y-%m-%d %H:%M}"


class ChatMessageRead(models.Model):
    """Xabarlarni o'qilgan/o'qilmagan holati"""
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='read_status')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']

    def __str__(self):
        return f"{self.user} read {self.message} at {self.read_at:%Y-%m-%d %H:%M}"


# ── Student Transfer ──────────────────────────────────────────────────
class StudentTransfer(models.Model):
    """O'quvchini boshqa sinfga ko'chirish yoki maktabdan chiqarish"""
    TRANSFER_TYPE = [
        ('class_transfer', 'Sinf o\'zgartirish'),
        ('school_transfer', 'Maktab o\'zgartirish'),
        ('graduation', 'Tamomlash'),
        ('withdrawal', 'Chiqarish'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transfers')
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPE)
    from_classroom = models.ForeignKey(Classroom, null=True, blank=True, on_delete=models.SET_NULL, related_name='transfers_out')
    to_classroom = models.ForeignKey(Classroom, null=True, blank=True, on_delete=models.SET_NULL, related_name='transfers_in')
    reason = models.TextField(blank=True)
    transfer_date = models.DateField(default=timezone.now)
    transferred_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transfer_date']
    
    def __str__(self):
        return f"{self.student} | {self.get_transfer_type_display()} | {self.transfer_date}"


# ── Online Payment Gateway ────────────────────────────────────────────
class OnlinePayment(models.Model):
    """O'zbekiston to'lov tizimlari orqali kelgan to'lovlar"""
    PROVIDER_CHOICES = [
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('uzum', 'Uzum Bank'),
        ('apelsin', 'Apelsin'),
        ('humo', 'Humo'),
        ('uzcard', 'UzCard'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('paid', 'To\'landi'),
        ('failed', 'Xato'),
        ('cancelled', 'Bekor qilindi'),
        ('refunded', 'Qaytarildi'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    transaction_id = models.CharField(max_length=200, unique=True)
    order_id = models.CharField(max_length=100, blank=True, help_text='Tizim ichki order ID')
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL, related_name='online_payments')
    contract = models.ForeignKey(Contract, null=True, blank=True, on_delete=models.SET_NULL, related_name='online_payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    month_for = models.DateField(null=True, blank=True)
    raw_request = models.JSONField(null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)
    payment = models.OneToOneField(Payment, null=True, blank=True, on_delete=models.SET_NULL, related_name='online_payment')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.provider} | {self.transaction_id} | {self.amount} | {self.status}"
