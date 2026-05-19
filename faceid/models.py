from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CameraConfig(models.Model):
    """Brauzer/web-kamera sozlamalari (kompyuterga ulangan kamera)."""

    SCOPE_CHOICES = [
        ('students', "O'quvchilar"),
        ('hr', 'Xodimlar (HR)'),
        ('shared', 'Umumiy kirish kamerasi'),
    ]

    name = models.CharField(max_length=120, help_text="Masalan: Kirish eshigi, 1-sinf")
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='students')
    device_id = models.CharField(
        max_length=512,
        blank=True,
        help_text="navigator.mediaDevices deviceId (brauzerda saqlanadi)",
    )
    device_label = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scope', '-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_scope_display()})"

    def save(self, *args, **kwargs):
        if self.is_default:
            CameraConfig.objects.filter(scope=self.scope, is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)


class FaceProfile(models.Model):
    """Yuz encoding — o'quvchi yoki xodim bilan bog'langan."""

    PERSON_STUDENT = 'student'
    PERSON_EMPLOYEE = 'employee'
    PERSON_CHOICES = [
        (PERSON_STUDENT, "O'quvchi"),
        (PERSON_EMPLOYEE, 'Xodim'),
    ]

    person_type = models.CharField(max_length=20, choices=PERSON_CHOICES)
    student = models.ForeignKey(
        'students.Student',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='face_profiles',
    )
    employee = models.ForeignKey(
        'hr.Employee',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='face_profiles',
    )
    encoding = models.JSONField(help_text='128 o\'lchamli yuz vektori')
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.person_type == self.PERSON_STUDENT and self.student_id:
            return f"FACE: {self.student}"
        if self.person_type == self.PERSON_EMPLOYEE and self.employee_id:
            return f"FACE: {self.employee}"
        return f"FACE profile #{self.pk}"


class FaceCheckLog(models.Model):
    """Har bir tanish / urinish yozuvi."""

    RESULT_MATCH = 'matched'
    RESULT_UNKNOWN = 'unknown'
    RESULT_NO_FACE = 'no_face'
    RESULT_ERROR = 'error'
    RESULT_CHOICES = [
        (RESULT_MATCH, 'Tanildi'),
        (RESULT_UNKNOWN, 'Noma\'lum'),
        (RESULT_NO_FACE, 'Yuz topilmadi'),
        (RESULT_ERROR, 'Xato'),
    ]

    camera = models.ForeignKey(CameraConfig, null=True, blank=True, on_delete=models.SET_NULL)
    scope = models.CharField(max_length=20, blank=True)
    person_type = models.CharField(max_length=20, blank=True)
    student = models.ForeignKey(
        'students.Student', null=True, blank=True, on_delete=models.SET_NULL, related_name='face_checks'
    )
    employee = models.ForeignKey(
        'hr.Employee', null=True, blank=True, on_delete=models.SET_NULL, related_name='face_checks'
    )
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    confidence = models.FloatField(null=True, blank=True, help_text='Masofa (kichik = yaxshi)')
    attendance_marked = models.BooleanField(default=False)
    message = models.CharField(max_length=255, blank=True)
    checked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-checked_at']

    def __str__(self):
        return f"{self.get_result_display()} @ {self.checked_at:%H:%M:%S}"
