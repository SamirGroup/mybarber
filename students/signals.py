from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    Student, Classroom, Contract, StudentBalance, MonthlyPayment,
    ChatGroup, Schedule
)


@receiver(post_save, sender=Student)
def create_student_balance(sender, instance, created, **kwargs):
    """O'quvchi yaratilganda avtomatik balans yaratish"""
    if created:
        StudentBalance.objects.get_or_create(student=instance)


@receiver(post_save, sender=Student)
def assign_to_classroom(sender, instance, created, **kwargs):
    """O'quvchi sinfga biriktirilganda avtomatik amallar"""
    if instance.classroom and created:
        # Avtomatik sinf chat guruhiga qo'shish
        classroom = instance.classroom
        
        # Sinf chat guruhini topish yoki yaratish
        chat_group, _ = ChatGroup.objects.get_or_create(
            name=f"{classroom.name} - Sinf guruhi",
            group_type='classroom',
            classroom=classroom,
            defaults={'is_active': True}
        )
        
        # O'quvchini guruhga qo'shish
        chat_group.students.add(instance)


@receiver(post_save, sender=Contract)
def create_monthly_payments(sender, instance, created, **kwargs):
    """Shartnoma yaratilganda avtomatik oylik to'lovlar yaratish"""
    if created and instance.is_active:
        # Joriy oydan boshlab 12 oylik to'lov yaratish
        today = timezone.now().date()
        current_month = today.replace(day=1)
        
        for i in range(12):
            month = current_month.replace(
                year=current_month.year + (current_month.month + i - 1) // 12,
                month=(current_month.month + i - 1) % 12 + 1
            )
            
            # To'lov muddati (oyning 10-kuni)
            due_date = month.replace(day=10)
            
            MonthlyPayment.objects.get_or_create(
                contract=instance,
                month=month,
                defaults={
                    'amount_due': instance.effective_fee,
                    'due_date': due_date,
                    'status': 'pending'
                }
            )


@receiver(post_save, sender=Classroom)
def create_classroom_chat_group(sender, instance, created, **kwargs):
    """Sinf yaratilganda avtomatik chat guruhi yaratish"""
    if created:
        ChatGroup.objects.get_or_create(
            name=f"{instance.name} - Sinf guruhi",
            group_type='classroom',
            classroom=instance,
            defaults={'is_active': True}
        )


@receiver(m2m_changed, sender=ChatGroup.members.through)
def add_homeroom_teacher_to_chat(sender, instance, action, **kwargs):
    """Sinf rahbarini avtomatik chat guruhga qo'shish"""
    if action == 'post_add' and instance.group_type == 'classroom':
        if instance.classroom and instance.classroom.homeroom_teacher:
            instance.members.add(instance.classroom.homeroom_teacher)
