from datetime import timedelta
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from enrollment.models import (
    LeadSource, Grade, AcademicYear, Lead, 
    CallRecord, StudentApplication, AgentProfile
)


class Command(BaseCommand):
    help = "Xususiy maktab qabul bo'limi uchun demo ma'lumot (leadlar, arizalar, lead manbalari)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing enrollment data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._clear_enrollment_data()
            self.stdout.write(self.style.WARNING("Existing enrollment data cleared."))

        self._ensure_groups()
        sources = self._seed_sources()
        grades = self._seed_grades()
        academic_year = self._seed_academic_year()
        leads = self._seed_leads(sources, grades)
        self._seed_applications(leads, grades)
        self._seed_call_records(leads)

        self.stdout.write(self.style.SUCCESS("Private school enrollment demo data seeded successfully."))

    def _clear_enrollment_data(self):
        StudentApplication.objects.all().delete()
        CallRecord.objects.all().delete()
        Lead.objects.all().delete()
        AcademicYear.objects.all().delete()
        Grade.objects.all().delete()
        LeadSource.objects.all().delete()

    def _ensure_groups(self):
        for name in ('enrollment_agent', 'enrollment_manager'):
            Group.objects.get_or_create(name=name)

    def _seed_sources(self):
        sources_data = [
            {'name': 'Meta (Facebook/Instagram)', 'code': 'meta'},
            {'name': 'Veb-sayt', 'code': 'website'},
            {'name': 'Telefon qo\'ng\'iroq', 'code': 'phone'},
            {'name': 'Tavsiqa', 'code': 'referral'},
            {'name': 'Ochiq kun', 'code': 'open_day'},
            {'name': 'Reklama', 'code': 'advertisement'},
            {'name': 'Boshqa', 'code': 'other'},
        ]
        objects = {}
        for data in sources_data:
            obj, _ = LeadSource.objects.update_or_create(
                code=data['code'],
                defaults={'name': data['name']}
            )
            objects[data['code']] = obj
        return objects

    def _seed_grades(self):
        grades_data = [
            {'name': '1-sinf', 'sort_order': 1},
            {'name': '2-sinf', 'sort_order': 2},
            {'name': '3-sinf', 'sort_order': 3},
            {'name': '4-sinf', 'sort_order': 4},
            {'name': '5-sinf', 'sort_order': 5},
            {'name': '6-sinf', 'sort_order': 6},
            {'name': '7-sinf', 'sort_order': 7},
            {'name': '8-sinf', 'sort_order': 8},
            {'name': '9-sinf', 'sort_order': 9},
            {'name': '10-sinf', 'sort_order': 10},
            {'name': '11-sinf', 'sort_order': 11},
        ]
        objects = {}
        for data in grades_data:
            obj, _ = Grade.objects.update_or_create(
                name=data['name'],
                defaults={'sort_order': data['sort_order']}
            )
            objects[data['sort_order']] = obj
        return objects

    def _seed_academic_year(self):
        year, _ = AcademicYear.objects.update_or_create(
            name='2025-2026',
            defaults={
                'start_date': timezone.now().date().replace(month=9, day=1),
                'end_date': timezone.now().date().replace(year=timezone.now().year + 1, month=6, day=15),
                'is_current': True,
            }
        )
        return year

    def _seed_leads(self, sources, grades):
        leads_data = [
            {'first_name': 'Aziz', 'last_name': 'Karimov', 'phone': '+998901234567', 'email': 'azize@example.com', 
             'child_name': 'Ali', 'child_age': 7, 'grade': 1, 'source': 'meta', 'status': 'new'},
            {'first_name': 'Malika', 'last_name': 'Usmonova', 'phone': '+998912345678', 'email': 'malika@example.com',
             'child_name': 'Dilshod', 'child_age': 9, 'grade': 3, 'source': 'referral', 'status': 'contacted'},
            {'first_name': 'Bobur', 'last_name': 'Abdullayev', 'phone': '+998923456789', 'email': 'bobur@example.com',
             'child_name': 'Sherzod', 'child_age': 11, 'grade': 5, 'source': 'website', 'status': 'interested'},
            {'first_name': 'Gulnora', 'last_name': 'Toshpulatova', 'phone': '+998934567890',
             'child_name': 'Nilufar', 'child_age': 6, 'grade': 0, 'source': 'open_day', 'status': 'appointment'},
            {'first_name': 'Samir', 'last_name': 'Nazarov', 'phone': '+998945678901', 'email': 'samir@example.com',
             'child_name': 'Azamat', 'child_age': 14, 'grade': 8, 'source': 'meta', 'status': 'new'},
            {'first_name': 'Dilorom', 'last_name': 'Rahimova', 'phone': '+998956789012',
             'child_name': 'Ulug\'bek', 'child_age': 8, 'grade': 2, 'source': 'phone', 'status': 'contacted'},
            {'first_name': 'Jasur', 'last_name': 'Qurbonov', 'phone': '+998967890123', 'email': 'jasur@example.com',
             'child_name': 'Sarvar', 'child_age': 16, 'grade': 10, 'source': 'advertisement', 'status': 'new'},
            {'first_name': 'Nilufar', 'last_name': 'Ahmedova', 'phone': '+998978901234',
             'child_name': 'Madina', 'child_age': 10, 'grade': 4, 'source': 'referral', 'status': 'registered'},
        ]
        
        objects = []
        for i, data in enumerate(leads_data):
            lead = Lead.objects.create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data['phone'],
                email=data.get('email'),
                child_name=data['child_name'],
                child_age=data['child_age'],
                interested_grade=grades.get(data['grade']),
                source=sources[data['source']],
                status=data['status'],
                meta_lead_id=f'meta_lead_{i+1}' if data['source'] == 'meta' else None,
                created_at=timezone.now() - timedelta(days=i),
            )
            objects.append(lead)
        return objects

    def _seed_applications(self, leads, grades):
        applications_data = [
            {'lead_index': 7, 'student_first': 'Madina', 'student_last': 'Ahmedova', 
             'grade': 4, 'status': 'enrolled', 'fee_paid': True},
            {'lead_index': 2, 'student_first': 'Sherzod', 'student_last': 'Abdullayev',
             'grade': 5, 'status': 'approved', 'fee_paid': True},
        ]
        
        for data in applications_data:
            lead = leads[data['lead_index']]
            StudentApplication.objects.create(
                lead=lead,
                parent_first_name=lead.first_name,
                parent_last_name=lead.last_name,
                parent_phone=lead.phone,
                parent_email=lead.email,
                parent_relation='Ota',
                student_first_name=data['student_first'],
                student_last_name=data['student_last'],
                student_dob=timezone.now().date() - timedelta(days=data['grade']*365),
                student_gender='F' if data['student_first'] == 'Madina' else 'M',
                applying_grade=grades.get(data['grade']),
                status=data['status'],
                application_fee_paid=data['fee_paid'],
                application_fee_amount=500000 if data['fee_paid'] else 0,
                submitted_at=timezone.now() - timedelta(days=2) if data['status'] != 'draft' else None,
            )

    def _seed_call_records(self, leads):
        call_data = [
            {'lead_index': 0, 'direction': 'outbound', 'status': 'completed', 'duration': 180},
            {'lead_index': 1, 'direction': 'outbound', 'status': 'completed', 'duration': 240},
            {'lead_index': 2, 'direction': 'outbound', 'status': 'completed', 'duration': 120},
            {'lead_index': 5, 'direction': 'inbound', 'status': 'completed', 'duration': 300},
        ]
        
        for data in call_data:
            lead = leads[data['lead_index']]
            CallRecord.objects.create(
                lead=lead,
                agent=lead.assigned_to,
                caller_number='+998901234567' if data['direction'] == 'outbound' else lead.phone,
                callee_number=lead.phone if data['direction'] == 'outbound' else '+998901234567',
                direction=data['direction'],
                status=data['status'],
                duration_seconds=data['duration'],
                started_at=timezone.now() - timedelta(hours=data['lead_index']+1),
                ended_at=timezone.now() - timedelta(hours=data['lead_index']+1) + timedelta(seconds=data['duration']),
            )