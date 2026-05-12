"""
Call Centre demo ma'lumotlarini yaratish.
python manage.py shell < create_call_centre_demo.py
"""
from django.contrib.auth.models import User, Group
from enrollment.models import (
    LeadSource, Grade, Lead, AgentProfile, CallRecord, 
    CallRouting, LeadComment
)
from django.utils import timezone
import random

# 1. Guruhlar yaratish
enrollment_agent, _ = Group.objects.get_or_create(name='enrollment_agent')
enrollment_manager, _ = Group.objects.get_or_create(name='enrollment_manager')
enrollment_supervisor, _ = Group.objects.get_or_create(name='enrollment_supervisor')

print("✓ Guruhlar yaratildi")

# 2. Operatorlar yaratish
operators_data = [
    {'username': 'operator_sarvar', 'first_name': 'Sarvar', 'last_name': 'Karimov', 'phone': '+998901234567'},
    {'username': 'operator_dilnoza', 'first_name': 'Dilnoza', 'last_name': 'Yusupova', 'phone': '+998901234568'},
    {'username': 'operator_aziz', 'first_name': 'Aziz', 'last_name': 'Rahimov', 'phone': '+998901234569'},
]

for op_data in operators_data:
    user, created = User.objects.get_or_create(
        username=op_data['username'],
        defaults={
            'first_name': op_data['first_name'],
            'last_name': op_data['last_name'],
            'email': f"{op_data['username']}@school.uz",
        }
    )
    if created:
        user.set_password('operator123')
        user.save()
    
    user.groups.add(enrollment_agent)
    
    # Agent profil yaratish
    agent, _ = AgentProfile.objects.get_or_create(
        user=user,
        defaults={
            'extension': str(1000 + User.objects.filter(groups=enrollment_agent).count()),
            'phone_number': op_data['phone'],
            'status': 'online',
            'is_available': True,
        }
    )
    
    print(f"✓ Operator yaratildi: {user.username}")

# 3. Supervisor yaratish
supervisor, created = User.objects.get_or_create(
    username='supervisor_admin',
    defaults={
        'first_name': 'Admin',
        'last_name': 'Supervisor',
        'email': 'supervisor@school.uz',
        'is_staff': True,
    }
)
if created:
    supervisor.set_password('supervisor123')
    supervisor.save()
supervisor.groups.add(enrollment_manager, enrollment_supervisor)
print("✓ Supervisor yaratildi")

# 4. Lead Source yaratish
meta_source, _ = LeadSource.objects.get_or_create(
    code='meta',
    defaults={'name': 'Meta (Facebook/Instagram)'}
)
phone_source, _ = LeadSource.objects.get_or_create(
    code='phone',
    defaults={'name': 'Telefon qo\'ng\'iroq'}
)
web_source, _ = LeadSource.objects.get_or_create(
    code='web',
    defaults={'name': 'Veb-sayt'}
)
print("✓ Lead sources yaratildi")

# 5. Grades yaratish
grades_data = ['1-A', '1-B', '2-A', '2-B', '3-A', '3-B', '4-A', '5-A']
for i, grade_name in enumerate(grades_data):
    Grade.objects.get_or_create(
        name=grade_name,
        defaults={'sort_order': i}
    )
print("✓ Grades yaratildi")

# 6. Call Routing yaratish
routing, _ = CallRouting.objects.get_or_create(
    phone_number='+998712345678',
    defaults={
        'name': 'Asosiy qabul liniyasi',
        'strategy': 'round_robin',
        'is_active': True,
        'business_hours_only': True,
        'business_hours_start': '09:00',
        'business_hours_end': '18:00',
        'max_queue_size': 50,
        'max_wait_time_seconds': 300,
        'welcome_message': 'Bunyod Non Sharjah School qabul bo\'limiga xush kelibsiz.',
    }
)
print("✓ Call routing yaratildi")

# 7. Demo Leadlar yaratish
leads_data = [
    {
        'first_name': 'Dilnoza',
        'last_name': 'Yusupova',
        'phone': '+998911234567',
        'phone_2': '+998978069833',
        'region': 'Namangan',
        'children_count': 1,
        'interested_grade': '1-A',
        'source': meta_source,
        'meta_campaign_name': 'New Academic Year',
        'meta_adset_name': 'Parents 25-45',
        'meta_form_name': 'Open Day RSVP',
        'status': 'contacted',
    },
    {
        'first_name': 'Aziza',
        'last_name': 'Karimova',
        'phone': '+998901111111',
        'region': 'Toshkent',
        'children_count': 2,
        'interested_grade': '2-A',
        'source': phone_source,
        'status': 'new',
    },
    {
        'first_name': 'Bobur',
        'last_name': 'Rahimov',
        'phone': '+998902222222',
        'region': 'Samarqand',
        'children_count': 1,
        'interested_grade': '3-A',
        'source': web_source,
        'status': 'interested',
    },
]

agents = list(User.objects.filter(groups=enrollment_agent))

for lead_data in leads_data:
    grade_name = lead_data.pop('interested_grade')
    grade = Grade.objects.filter(name=grade_name).first()
    
    lead, created = Lead.objects.get_or_create(
        phone=lead_data['phone'],
        defaults={
            **lead_data,
            'interested_grade': grade,
            'assigned_to': random.choice(agents) if agents else None,
            'discount_info': f"{(lead_data['children_count'] - 1) * 10}% chegirma" if lead_data['children_count'] > 1 else "Chegirma yo'q",
        }
    )
    
    if created:
        # Izoh qo'shish
        LeadComment.objects.create(
            lead=lead,
            user=random.choice(agents) if agents else supervisor,
            comment=f"Called parent {lead.full_name}. Interested in {grade_name} for {lead.children_count} child(ren)."
        )
        print(f"✓ Lead yaratildi: {lead.full_name}")

# 8. Demo qo'ng'iroqlar yaratish
for lead in Lead.objects.all()[:5]:
    agent = lead.assigned_to or random.choice(agents)
    
    call = CallRecord.objects.create(
        lead=lead,
        agent=agent,
        caller_number=lead.phone,
        callee_number='+998712345678',
        direction='inbound',
        status='completed',
        recording_consent='accepted',
        duration_seconds=random.randint(120, 600),
        talk_time_seconds=random.randint(100, 500),
        wait_time_seconds=random.randint(5, 30),
        started_at=timezone.now() - timezone.timedelta(hours=random.randint(1, 48)),
        answered_at=timezone.now() - timezone.timedelta(hours=random.randint(1, 48)),
        ended_at=timezone.now() - timezone.timedelta(hours=random.randint(0, 47)),
        disposition='interested',
        notes='Mijoz maktab haqida ma\'lumot oldi.',
    )
    print(f"✓ Qo'ng'iroq yaratildi: {call.caller_number}")

print("\n" + "="*50)
print("✅ DEMO MA'LUMOTLAR MUVAFFAQIYATLI YARATILDI!")
print("="*50)
print("\nLogin ma'lumotlari:")
print("-" * 50)
print("Operatorlar:")
print("  Username: operator_sarvar | Password: operator123")
print("  Username: operator_dilnoza | Password: operator123")
print("  Username: operator_aziz | Password: operator123")
print("\nSupervisor:")
print("  Username: supervisor_admin | Password: supervisor123")
print("-" * 50)
