from datetime import timedelta, date
from decimal import Decimal
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from students.models import (
    Classroom, Student, Parent, DocumentType, Subject,
    Schedule, Quarter, DailyGrade, QuarterGrade,
    Attendance, Homework, Contract, Payment,
    SmsNotificationConfig, ChatGroup
)
from enrollment.models import Grade, AcademicYear


class Command(BaseCommand):
    help = "O'quvchilar bo'limi uchun demo ma'lumot"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing students data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._clear_students_data()
            self.stdout.write(self.style.WARNING("Existing students data cleared."))

        self._ensure_groups()
        academic_year = self._seed_academic_year()
        grades = self._seed_grades()
        classrooms = self._seed_classrooms(grades, academic_year)
        subjects = self._seed_subjects()
        parents = self._seed_parents()
        students = self._seed_students(classrooms, parents)
        self._seed_contracts(students)
        self._seed_payments(students)
        self._seed_doc_types()
        self._seed_quarters(academic_year)
        self._seed_schedules(classrooms, subjects)
        self._seed_grades_data(students, subjects)
        self._seed_attendance(students)
        self._seed_homework(classrooms, subjects)
        self._seed_sms_config()
        self._seed_chat_groups(classrooms, students)

        self.stdout.write(self.style.SUCCESS("Students demo data seeded successfully."))

    def _clear_students_data(self):
        ChatGroup.objects.all().delete()
        SmsNotificationConfig.objects.all().delete()
        Payment.objects.all().delete()
        Contract.objects.all().delete()
        Homework.objects.all().delete()
        Attendance.objects.all().delete()
        QuarterGrade.objects.all().delete()
        DailyGrade.objects.all().delete()
        Quarter.objects.all().delete()
        Schedule.objects.all().delete()
        Student.objects.all().delete()
        Parent.objects.all().delete()
        Classroom.objects.all().delete()
        Subject.objects.all().delete()
        DocumentType.objects.all().delete()

    def _ensure_groups(self):
        for name in ('students_agent', 'students_manager'):
            Group.objects.get_or_create(name=name)

    def _seed_academic_year(self):
        year, _ = AcademicYear.objects.get_or_create(
            name='2025-2026',
            defaults={
                'start_date': date(2025, 9, 1),
                'end_date': date(2026, 6, 15),
                'is_current': True,
            }
        )
        return year

    def _seed_grades(self):
        grades = {}
        for i in range(1, 12):
            grade, _ = Grade.objects.get_or_create(
                name=f'{i}-sinf',
                defaults={'sort_order': i}
            )
            grades[i] = grade
        return grades

    def _seed_classrooms(self, grades, academic_year):
        classrooms = []
        for i in [1, 5, 9]:
            for letter in ['A', 'B']:
                classroom = Classroom.objects.create(
                    name=f'{i}-{letter}',
                    grade=grades[i],
                    academic_year=academic_year,
                    capacity=30
                )
                classrooms.append(classroom)
        return classrooms

    def _seed_subjects(self):
        subjects_list = [
            'Matematika', 'Ona tili', 'Ingliz tili', 'Fizika',
            'Kimyo', 'Biologiya', 'Tarix', 'Geografiya',
            'Informatika', 'Jismoniy tarbiya'
        ]
        subjects = []
        for name in subjects_list:
            subject, _ = Subject.objects.get_or_create(name=name)
            subjects.append(subject)
        return subjects

    def _seed_parents(self):
        parents_data = [
            {'first': 'Aziz', 'last': 'Karimov', 'phone': '+998901234567', 'relation': 'Ota'},
            {'first': 'Malika', 'last': 'Usmonova', 'phone': '+998912345678', 'relation': 'Ona'},
            {'first': 'Bobur', 'last': 'Abdullayev', 'phone': '+998923456789', 'relation': 'Ota'},
            {'first': 'Gulnora', 'last': 'Toshpulatova', 'phone': '+998934567890', 'relation': 'Ona'},
            {'first': 'Samir', 'last': 'Nazarov', 'phone': '+998945678901', 'relation': 'Ota'},
        ]
        parents = []
        for data in parents_data:
            parent = Parent.objects.create(
                first_name=data['first'],
                last_name=data['last'],
                phone=data['phone'],
                relation=data['relation']
            )
            parents.append(parent)
        return parents

    def _seed_students(self, classrooms, parents):
        students_data = [
            {'first': 'Ali', 'last': 'Karimov', 'middle': 'Azizovich', 'gender': 'M', 'birth': date(2015, 3, 15), 'classroom': 0, 'parent': 0},
            {'first': 'Dilshod', 'last': 'Usmonov', 'middle': 'Boburovich', 'gender': 'M', 'birth': date(2015, 5, 20), 'classroom': 0, 'parent': 1},
            {'first': 'Sherzod', 'last': 'Abdullayev', 'middle': 'Boburovich', 'gender': 'M', 'birth': date(2011, 7, 10), 'classroom': 2, 'parent': 2},
            {'first': 'Nilufar', 'last': 'Toshpulatova', 'middle': 'Samirovna', 'gender': 'F', 'birth': date(2011, 9, 25), 'classroom': 2, 'parent': 3},
            {'first': 'Azamat', 'last': 'Nazarov', 'middle': 'Samirovich', 'gender': 'M', 'birth': date(2007, 11, 5), 'classroom': 4, 'parent': 4},
        ]
        students = []
        for i, data in enumerate(students_data):
            student = Student.objects.create(
                first_name=data['first'],
                last_name=data['last'],
                middle_name=data['middle'],
                gender=data['gender'],
                birth_date=data['birth'],
                passport_or_id=f'AA{1234567 + i}',
                erp_number=f'ERP-2025-{1000 + i}',
                classroom=classrooms[data['classroom']],
                is_active=True
            )
            student.parents.add(parents[data['parent']])
            students.append(student)
        return students

    def _seed_contracts(self, students):
        for i, student in enumerate(students):
            Contract.objects.create(
                student=student,
                contract_number=f'SH-2025-{1001 + i}',
                start_date=date(2025, 9, 1),
                monthly_fee=Decimal('1500000'),
                discount_percent=Decimal('10') if i % 2 == 0 else Decimal('0'),
                discount_reason='Ikkinchi farzand' if i % 2 == 0 else '',
                is_active=True
            )

    def _seed_payments(self, students):
        today = timezone.now().date()
        for i, student in enumerate(students):
            contract = student.contracts.first()
            if i < 3:  # First 3 students paid
                Payment.objects.create(
                    student=student,
                    contract=contract,
                    amount=contract.effective_fee,
                    method='card',
                    payment_date=today,
                    month_for=today.replace(day=1)
                )

    def _seed_doc_types(self):
        doc_types = [
            'Tug\'ilganlik haqida guvohnoma',
            'Pasport nusxasi',
            'Tibbiy ma\'lumotnoma',
            'Tabel',
            'Oldingi maktab ma\'lumotnomasi',
        ]
        for name in doc_types:
            DocumentType.objects.get_or_create(name=name)

    def _seed_quarters(self, academic_year):
        quarters_data = [
            {'num': 1, 'start': date(2025, 9, 1), 'end': date(2025, 11, 15)},
            {'num': 2, 'start': date(2025, 11, 16), 'end': date(2026, 1, 31)},
            {'num': 3, 'start': date(2026, 2, 1), 'end': date(2026, 4, 15)},
            {'num': 4, 'start': date(2026, 4, 16), 'end': date(2026, 6, 15)},
        ]
        for data in quarters_data:
            Quarter.objects.get_or_create(
                academic_year=academic_year,
                number=data['num'],
                defaults={'start_date': data['start'], 'end_date': data['end']}
            )

    def _seed_schedules(self, classrooms, subjects):
        for classroom in classrooms[:2]:
            for i, subject in enumerate(subjects[:5]):
                Schedule.objects.create(
                    classroom=classroom,
                    subject=subject,
                    day_of_week=(i % 5) + 1,
                    start_time='08:00',
                    end_time='08:45'
                )

    def _seed_grades_data(self, students, subjects):
        for student in students:
            for subject in subjects[:3]:
                DailyGrade.objects.create(
                    student=student,
                    subject=subject,
                    grade=Decimal('4.5'),
                    date=timezone.now().date()
                )

    def _seed_attendance(self, students):
        today = timezone.now().date()
        for student in students:
            for i in range(5):
                Attendance.objects.create(
                    student=student,
                    date=today - timedelta(days=i),
                    status='present'
                )

    def _seed_homework(self, classrooms, subjects):
        for classroom in classrooms[:2]:
            for subject in subjects[:2]:
                Homework.objects.create(
                    classroom=classroom,
                    subject=subject,
                    title=f'{subject.name} uy vazifasi',
                    description='Test uy vazifasi',
                    due_date=timezone.now().date() + timedelta(days=7)
                )

    def _seed_sms_config(self):
        SmsNotificationConfig.objects.get_or_create(
            defaults={
                'day_of_month': 5,
                'is_active': True,
            }
        )

    def _seed_chat_groups(self, classrooms, students):
        for classroom in classrooms[:2]:
            chat = ChatGroup.objects.create(
                name=f'{classroom.name} guruhi',
                classroom=classroom
            )
            chat.students.add(*students[:3])
