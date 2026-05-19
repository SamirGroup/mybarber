from django.db.models.signals import post_save
from django.dispatch import receiver

from students.models import Student
from hr.models import Employee
from . import services
from .models import FaceProfile


@receiver(post_save, sender=Student)
def enroll_student_face(sender, instance, **kwargs):
    if instance.photo and instance.is_active:
        services.enroll_person(FaceProfile.PERSON_STUDENT, instance)


@receiver(post_save, sender=Employee)
def enroll_employee_face(sender, instance, **kwargs):
    if instance.photo and instance.status == 'active':
        services.enroll_person(FaceProfile.PERSON_EMPLOYEE, instance)
