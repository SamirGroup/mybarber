from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from students.models import (
    Classroom, Student, Parent, DocumentType, Subject, Schedule,
    Quarter, DailyGrade, QuarterGrade, Attendance, Homework,
    Contract, Payment, SmsNotificationConfig, ChatGroup, ChatMessage
)
from enrollment.models import Grade, AcademicYear


class Command(BaseCommand):
    help = "Students moduli uchun demo ma'lumotlar"

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Mavjud ma\'lumotlarni o\'chirish')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            self._clear_data()
            self.stdout.write(self.style.WARNING('Mavjud ma\'lumotlar o\'chirildi'))

        # Seed data
        academic_year = self._seed_academic_year()
        grades = self._seed_grades()
        quarters = self._seed_quarters(academic_year)
        subjects = self._seed_subjects()
        classrooms = self._seed_classrooms(academic_year, grades)
        parents = self._seed_parents()
        students = self._seed_students(classrooms, parents)
        self._seed_schedules(classrooms, subjects)
        self._seed_daily_grades(students, subjects)
        self._seed_quarter_grades(students, subjects, quarters)
        self._seed_attendance(students, subjects)
        self._seed_homework(classrooms, subjects)
        self._seed_contracts(students)
        self._seed_payments(students)
        self._seed_doc_types()
        self._seed_sms_config()
        self._seed_chat_groups(classrooms, students)

        self.stdout.write(self.style.SUCCESS('Students demo ma\'lumotlari muvaffaqiyatli yaratildi'))

    def _clear_data(self):
        ChatMessage.objects.all().delete()
        ChatGroup.objects.all().delete()
        Payment.objects.all().delete()
        Contract.objects.all().delete()
        Homework.objects.all().delete()
        Attendance.objects.all().delete()
        QuarterGrade.objects.all().delete()
        DailyGrade.objects.all().delete()
        Quarter.objects.all().delete()
        Schedule.objects.all().delete()
        DocumentType.objects.all().delete()
        Student.objects.all().delete()
        Parent.objects.all().delete()
        Classroom.objects.all().delete()
        Subject.objects.all().delete()

    def _seed_academic_year(self):
        year, _ = AcademicYear.objects.get_or_create(
            name='2024-2025',
            defaults={
                'start_date': timezone.now().date().replace(month=9, day=1),
                'end_date': timezone.now().date().replace(year=timezone.now().year + 1, month=6, day=30),
                'is_current': True
            }
        )
        return year

    def _seed_grades(self):
        grades_data = [
            ('1-sinf', 1), ('2-sinf', 2), ('3-sinf', 3), ('4-sinf', 4),
            ('5-sinf', 5), ('6-sinf', 6), ('7-sinf', 7), ('8-sinf', 8),
            ('9-sinf', 9), ('10-sinf', 10), ('11-sinf', 11)
        ]
        grades = []
        for name, order in grades_data:
            grade, _ = Grade.objects.get_or_create(name=name, defaults={'sort_order': order})
            grades.append(grade)
        return grades

    def _seed_quarters(self, academic_year):
        quarters_data = [
            (1, '2024-09-01', '2024-11-30'),
            (2, '2024-12-01', '2025-02-28'),
            (3, '2025-03-01', '2025-05-31'),
            (4, '2025-06-01', '2025-06-30'),
        ]
        quarters = []
        for num, start, end in quarters_data:
            quarter, _ = Quarter.objects.get_or_create(
                academic_year=academic_year,
                number=num,
                defaults={'start_date': start, 'end_date': end}
            )
            quarters.append(quarter)
        return quarters

    def _seed_subjects(self):
        subjects_data = [
            ('Matematika', 'MATH'),
            ('Ona tili', 'UZ'),
            ('Ingliz tili', 'ENG'),
            ('Fizika', 'PHYS'),
            ('Kimyo', 'CHEM'),
            ('Biologiya', 'BIO'),
            ('Tarix', 'HIST'),
            ('Geografiya', 'GEO'),
            ('Informatika', 'IT'),
            ('Jismoniy tarbiya', 'PE'),
        ]
        subjects = []
        for name, code in subjects_data:
            subject, _ = Subject.objects.get_or_create(name=name, defaults={'code': code})
            subjects.append(subject)
        return subjects

    def _seed_classrooms(self, academic_year, grades):
        classrooms = []
        for grade in grades[:6]:  # 1-6 sinflar
            for letter in ['A', 'B']:
                classroom, _ = Classroom.objects.get_or_create(
                    name=f"{grade.name.split('-')[0]}-{letter}",
                    academic_year=academic_year,
                    grade=grade,
                    defaults={'capacity': 30}
                )
                classrooms.append(classroom)
        return classrooms

    def _seed_parents(self):
        parents_data = [
            ('Aliyev', 'Bobur', '+998901234567', 'Ota'),
            ('Karimova', 'Dilnoza', '+998901234568', 'Ona'),
            ('Toshmatov', 'Sardor', '+998901234569', 'Ota'),
            ('Rahimova', 'Malika', '+998901234570', 'Ona'),
            ('Yusupov', 'Jamshid', '+998901234571', 'Ota'),
            ('Azimova', 'Nodira', '+998901234572', 'Ona'),
            ('Sharipov', 'Otabek', '+998901234573', 'Ota'),
            ('Mahmudova', 'Zarina', '+998901234574', 'Ona'),
            ('Ergashev', 'Rustam', '+998901234575', 'Ota'),
            ('Saidova', 'Gulnora', '+998901234576', 'Ona'),
        ]
        parents = []
        for last, first, phone, relation in parents_data:
            parent, _ = Parent.objects.get_or_create(
                phone=phone,
                defaults={'first_name': first, 'last_name': last, 'relation': relation}
            )
            parents.append(parent)
        return parents

    def _seed_students(self, classrooms, parents):
        students_data = [
            ('Aliyev', 'Ali', 'M', '2015-03-15'),
            ('Karimova', 'Kamila', 'F', '2015-05-20'),
            ('Toshmatov', 'Timur', 'M', '2014-08-10'),
            ('Rahimova', 'Ruxsora', 'F', '2014-11-25'),
            ('Yusupov', 'Yusuf', 'M', '2016-01-30'),
            ('Azimova', 'Aziza', 'F', '2016-04-12'),
            ('Sharipov', 'Shoxrux', 'M', '2015-07-18'),
            ('Mahmudova', 'Madina', 'F', '2015-09-22'),
            ('Ergashev', 'Eldor', 'M', '2014-12-05'),
            ('Saidova', 'Sabina', 'F', '2014-02-14'),
            ('Abdullayev', 'Abdulla', 'M', '2015-06-08'),
            ('Nurmatova', 'Nilufar', 'F', '2015-10-17'),
            ('Ismoilov', 'Islom', 'M', '2016-03-25'),
            ('Xolmatova', 'Xurshida', 'F', '2016-05-30'),
            ('Qodirov', 'Qodirjon', 'M', '2014-09-12'),
        ]
        students = []
        for i, (last, first, gender, birth) in enumerate(students_data):
            classroom = classrooms[i % len(classrooms)]
            student, _ = Student.objects.get_or_create(
                first_name=first,
                last_name=last,
                birth_date=birth,
                defaults={
                    'gender': gender,
                    'classroom': classroom,
                    'is_active': True,
                    'address': f'Toshkent shahar, {i+1}-ko\'cha, {i+10}-uy'
                }
            )
            # Add parents
            if i < len(parents):
                student.parents.add(parents[i])
            students.append(student)
        return students

    def _seed_schedules(self, classrooms, subjects):
        days = [1, 2, 3, 4, 5]  # Dushanba-Juma
        times = [
            ('08:00', '08:45'),
            ('09:00', '09:45'),
            ('10:00', '10:45'),
            ('11:00', '11:45'),
            ('13:00', '13:45'),
        ]
        
        for classroom in classrooms[:3]:  # Faqat birinchi 3 ta sinf uchun
            for day in days:
                for i, (start, end) in enumerate(times[:4]):
                    subject = subjects[i % len(subjects)]
                    Schedule.objects.get_or_create(
                        classroom=classroom,
                        subject=subject,
                        day_of_week=day,
                        start_time=start,
                        defaults={'end_time': end}
                    )

    def _seed_daily_grades(self, students, subjects):
        today = timezone.now().date()
        for student in students[:10]:
            for i in range(5):
                date = today - timedelta(days=i)
                subject = subjects[i % len(subjects)]
                DailyGrade.objects.get_or_create(
                    student=student,
                    subject=subject,
                    date=date,
                    defaults={'grade': Decimal('4.5'), 'comment': 'Yaxshi'}
                )

    def _seed_quarter_grades(self, students, subjects, quarters):
        for student in students[:10]:
            for subject in subjects[:5]:
                for quarter in quarters[:2]:
                    QuarterGrade.objects.get_or_create(
                        student=student,
                        subject=subject,
                        quarter=quarter,
                        defaults={'grade': Decimal('4.0')}
                    )

    def _seed_attendance(self, students, subjects):
        today = timezone.now().date()
        statuses = ['present', 'present', 'present', 'late', 'absent']
        
        for student in students[:10]:
            for i in range(7):
                date = today - timedelta(days=i)
                subject = subjects[i % len(subjects)]
                Attendance.objects.get_or_create(
                    student=student,
                    date=date,
                    subject=subject,
                    defaults={'status': statuses[i % len(statuses)]}
                )

    def _seed_homework(self, classrooms, subjects):
        today = timezone.now().date()
        for classroom in classrooms[:3]:
            for i in range(3):
                subject = subjects[i]
                Homework.objects.get_or_create(
                    classroom=classroom,
                    subject=subject,
                    title=f'{subject.name} uy vazifasi #{i+1}',
                    defaults={
                        'description': f'{subject.name} fanidan amaliy mashqlar',
                        'due_date': today + timedelta(days=i+1)
                    }
                )

    def _seed_contracts(self, students):
        for i, student in enumerate(students[:10]):
            Contract.objects.get_or_create(
                student=student,
                contract_number=f'2024-{1000+i}',
                defaults={
                    'start_date': timezone.now().date().replace(month=9, day=1),
                    'monthly_fee': Decimal('500000.00'),
                    'discount_percent': Decimal('0.00'),
                    'is_active': True
                }
            )

    def _seed_payments(self, students):
        today = timezone.now().date()
        for student in students[:8]:
            contract = student.contracts.first()
            if contract:
                Payment.objects.get_or_create(
                    student=student,
                    contract=contract,
                    payment_date=today,
                    defaults={
                        'amount': Decimal('500000.00'),
                        'method': 'cash',
                        'month_for': today
                    }
                )

    def _seed_doc_types(self):
        doc_types = [
            ('Pasport nusxasi', True),
            ('Tug\'ilganlik haqida guvohnoma', True),
            ('Tibbiy ma\'lumotnoma', True),
            ('3x4 fotosurat', True),
            ('Oldingi maktab ma\'lumotnomasi', False),
        ]
        for name, required in doc_types:
            DocumentType.objects.get_or_create(name=name, defaults={'is_required': required})

    def _seed_sms_config(self):
        SmsNotificationConfig.objects.get_or_create(
            id=1,
            defaults={
                'day_of_month': 5,
                'is_active': True,
                'message_template': 'Hurmatli {parent_name}! Farzandingiz {student_name} uchun {debt_amount} so\'m qarzdorlik mavjud.'
            }
        )

    def _seed_chat_groups(self, classrooms, students):
        for classroom in classrooms[:2]:
            chat, _ = ChatGroup.objects.get_or_create(
                name=f'{classroom.name} ota-onalar guruhi',
                defaults={'classroom': classroom}
            )
            # Add students from this classroom
            classroom_students = [s for s in students if s.classroom == classroom][:5]
            if classroom_students:
                chat.students.add(*classroom_students)
