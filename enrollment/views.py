from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import (
    Lead, LeadSource, Grade, AcademicYear, CallRecord,
    CallCampaign, StudentApplication, AgentProfile,
)
from django.contrib.auth.models import User, Group
import json


# ── Role helpers ──────────────────────────────────────────────────────
def _is_enrollment_staff(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['enrollment_agent', 'enrollment_manager']).exists()


def enrollment_required(view):
    return user_passes_test(_is_enrollment_staff, login_url='login')(login_required(view))


def _ensure_enrollment_groups():
    for name in ('enrollment_agent', 'enrollment_manager'):
        Group.objects.get_or_create(name=name)


# ── Dashboard ─────────────────────────────────────────────────────────
@login_required
@enrollment_required
def dashboard(request):
    _ensure_enrollment_groups()

    leads_total = Lead.objects.count()
    leads_new = Lead.objects.filter(status='new').count()
    leads_contacted = Lead.objects.filter(status='contacted').count()
    leads_registered = Lead.objects.filter(status='registered').count()

    applications_total = StudentApplication.objects.count()
    applications_pending = StudentApplication.objects.filter(
        status__in=['submitted', 'under_review', 'documents_pending']
    ).count()
    applications_approved = StudentApplication.objects.filter(status='approved').count()
    applications_enrolled = StudentApplication.objects.filter(status='enrolled').count()

    recent_leads = Lead.objects.select_related('source', 'interested_grade', 'assigned_to').order_by('-created_at')[:15]
    recent_applications = StudentApplication.objects.select_related('applying_grade', 'lead').order_by('-created_at')[:10]
    recent_calls = CallRecord.objects.select_related('lead', 'agent').order_by('-created_at')[:10]

    sources = LeadSource.objects.all()
    grades = Grade.objects.all()
    agents = User.objects.filter(groups__name='enrollment_agent').distinct()

    context = {
        'leads_total': leads_total,
        'leads_new': leads_new,
        'leads_contacted': leads_contacted,
        'leads_registered': leads_registered,
        'applications_total': applications_total,
        'applications_pending': applications_pending,
        'applications_approved': applications_approved,
        'applications_enrolled': applications_enrolled,
        'recent_leads': recent_leads,
        'recent_applications': recent_applications,
        'recent_calls': recent_calls,
        'sources': sources,
        'grades': grades,
        'agents': agents,
        'page_title': 'Qabul bo\'limi',
    }
    return render(request, 'enrollment/dashboard.html', context)


# ── Leads ─────────────────────────────────────────────────────────────
@login_required
@enrollment_required
def lead_list(request):
    status_filter = request.GET.get('status', '')
    source_filter = request.GET.get('source', '')
    search = request.GET.get('search', '')
    assigned = request.GET.get('assigned', '')

    leads = Lead.objects.select_related('source', 'interested_grade', 'assigned_to').all()

    if status_filter:
        leads = leads.filter(status=status_filter)
    if source_filter:
        leads = leads.filter(source_id=source_filter)
    if search:
        leads = leads.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(child_name__icontains=search)
        )
    if assigned == 'me':
        leads = leads.filter(assigned_to=request.user)
    elif assigned == 'unassigned':
        leads = leads.filter(assigned_to__isnull=True)

    paginator = Paginator(leads, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'source_filter': source_filter,
        'search': search,
        'assigned': assigned,
        'sources': LeadSource.objects.all(),
        'status_choices': Lead.LEAD_STATUS_CHOICES,
        'agents': User.objects.filter(groups__name='enrollment_agent').distinct(),
        'page_title': 'Leadlar',
    }
    return render(request, 'enrollment/lead_list.html', context)


@login_required
@enrollment_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead.objects.select_related('source', 'interested_grade', 'assigned_to'), pk=pk)
    calls = lead.calls.select_related('agent').order_by('-created_at')
    applications = lead.applications.select_related('applying_grade').order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update_status':
            lead.status = request.POST.get('status', lead.status)
            if lead.status == 'contacted' and not lead.contacted_at:
                lead.contacted_at = timezone.now()
            lead.save()
            messages.success(request, 'Lead holati yangilandi.')
            return redirect('enrollment_lead_detail', pk=lead.pk)
        elif action == 'update_notes':
            lead.notes = request.POST.get('notes', lead.notes)
            lead.save()
            messages.success(request, 'Eslatmalar saqlandi.')
            return redirect('enrollment_lead_detail', pk=lead.pk)
        elif action == 'assign':
            agent_id = request.POST.get('agent_id', '')
            if agent_id:
                lead.assigned_to_id = int(agent_id)
            else:
                lead.assigned_to = None
            lead.save()
            messages.success(request, 'Agent biriktirildi.' if agent_id else 'Agent olib tashlandi.')
            return redirect('enrollment_lead_detail', pk=lead.pk)
        elif action == 'create_application':
            return redirect('enrollment_application_create', lead_id=lead.pk)

    context = {
        'lead': lead,
        'calls': calls,
        'applications': applications,
        'status_choices': Lead.LEAD_STATUS_CHOICES,
        'agents': User.objects.filter(groups__name='enrollment_agent').distinct(),
        'grades': Grade.objects.all(),
        'page_title': f'Lead: {lead.full_name}',
    }
    return render(request, 'enrollment/lead_detail.html', context)


@login_required
@enrollment_required
def lead_create(request):
    if request.method == 'POST':
        lead = Lead(
            first_name=request.POST.get('first_name', '').strip(),
            last_name=request.POST.get('last_name', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            email=request.POST.get('email', '').strip() or None,
            child_name=request.POST.get('child_name', '').strip(),
            child_age=request.POST.get('child_age') or None,
            interested_grade_id=request.POST.get('grade') or None,
            source_id=request.POST.get('source') or None,
            notes=request.POST.get('notes', '').strip(),
            assigned_to=request.user,
        )
        lead.save()
        messages.success(request, f'Lead yaratildi: {lead.full_name}')
        return redirect('enrollment_lead_detail', pk=lead.pk)

    context = {
        'sources': LeadSource.objects.all(),
        'grades': Grade.objects.all(),
        'page_title': 'Yangi lead qo\'shish',
    }
    return render(request, 'enrollment/lead_form.html', context)


# ── Meta Lead Webhook ───────────────────────────────────────────────────
@csrf_exempt
@require_POST
def meta_lead_webhook(request):
    """Meta (Facebook/Instagram) dan lead'larni qabul qiluvchi webhook."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Meta Lead Ads formatiga moslashish (odatda leadgen webhook)
    # Bu yerda format soddalashtirilgan — real integrationda Meta ning formatiga moslanadi
    entries = data.get('entry', [])
    created = 0
    for entry in entries:
        changes = entry.get('changes', [])
        for change in changes:
            value = change.get('value', {})
            lead_data = value.get('lead_data', value)

            lead_source, _ = LeadSource.objects.get_or_create(
                code='meta',
                defaults={'name': 'Meta (Facebook/Instagram)'}
            )

            lead = Lead.objects.create(
                first_name=lead_data.get('first_name', lead_data.get('full_name', 'Noma\'lum')).split(' ')[0],
                last_name=' '.join(lead_data.get('first_name', lead_data.get('full_name', 'Noma\'lum')).split(' ')[1:]),
                phone=lead_data.get('phone_number', lead_data.get('phone', '')),
                email=lead_data.get('email', None),
                source=lead_source,
                meta_lead_id=str(value.get('leadgen_id', value.get('id', ''))),
                status='new',
            )
            created += 1

    return JsonResponse({'status': 'ok', 'created': created})


# ── Call Centre ───────────────────────────────────────────────────────
@login_required
@enrollment_required
def call_centre(request):
    """Call centre interfeysi — brauzer ichida IP telefoniya (Twilio asosida)."""
    agent, _ = AgentProfile.objects.get_or_create(user=request.user)

    recent_calls = CallRecord.objects.select_related('lead').filter(
        agent=request.user
    ).order_by('-created_at')[:20]

    active_calls = CallRecord.objects.filter(
        agent=request.user, status__in=['ringing', 'in_progress']
    )

    context = {
        'agent': agent,
        'recent_calls': recent_calls,
        'active_calls': active_calls,
        'page_title': 'Call Centre',
    }
    return render(request, 'enrollment/call_centre.html', context)


@login_required
@enrollment_required
def call_initiate(request):
    """Yangi qo'ng'iroq boshlash (Twilio orqali)."""
    if request.method == 'POST':
        to_number = request.POST.get('to_number', '').strip()
        lead_id = request.POST.get('lead_id', None)

        if not to_number:
            messages.error(request, 'Telefon raqam kiritilishi kerak.')
            return redirect('enrollment_call_centre')

        # Twilio call initiation — bu yerda Twilio REST API chaqiriladi
        # Hozircha record yaratamiz, Twilio keyin qo'shiladi
        lead = None
        if lead_id:
            lead = get_object_or_404(Lead, pk=lead_id)

        call = CallRecord.objects.create(
            lead=lead,
            agent=request.user,
            caller_number='+' + getattr(request.user, 'agent_profile', None).__str__() or '+998XXXXXXXX',
            callee_number=to_number,
            direction='outbound',
            status='ringing',
            started_at=timezone.now(),
        )

        # TODO: Twilio Client orqali qo'ng'iroq qilish
        messages.success(request, f'Qo\'ng\'iroq {to_number} raqamiga yo\'naltirildi.')
        return redirect('enrollment_call_centre')

    leads = Lead.objects.filter(status__in=['new', 'contacted', 'interested']).order_by('-created_at')[:50]
    context = {
        'leads': leads,
        'page_title': 'Qo\'ng\'iroq qilish',
    }
    return render(request, 'enrollment/call_initiate.html', context)


# ── Twilio TwiML endpoint (Twilio'dan webhook) ─────────────────────────
@csrf_exempt
@require_POST
def twilio_voice_webhook(request):
    """Twilio'dan kiruvchi/chiqish qo'ng'iroqlari uchun TwiML."""
    from django.http import HttpResponse
    from django.conf import settings

    call_sid = request.POST.get('CallSid', '')
    caller = request.POST.get('From', '')
    callee = request.POST.get('To', '')
    direction = 'inbound' if request.POST.get('Direction', 'inbound') == 'inbound' else 'outbound'

    # Call record yaratish/yangilash
    call_record, _ = CallRecord.objects.update_or_create(
        twilio_call_sid=call_sid,
        defaults={
            'caller_number': caller,
            'callee_number': callee,
            'direction': direction,
            'status': 'in_progress',
            'started_at': timezone.now(),
        }
    )

    # TwiML response — qo'ng'iroqni agentga ulash yoki yozib olish
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="uz-UZ">Bunyod Non Sharjah School maktabiga xush kelibsiz. Qabul bo'limiga ulanmoqdasiz.</Say>
    <Record timeout="10" transcribe="true" action="/enrollment/twilio/recording-status/" />
</Response>'''
    return HttpResponse(twiml, content_type='text/xml')


@csrf_exempt
@require_POST
def twilio_recording_status(request):
    """Twilio'dan yozuv holati webhook."""
    call_sid = request.POST.get('CallSid', '')
    recording_url = request.POST.get('RecordingUrl', '')
    recording_sid = request.POST.get('RecordingSid', '')
    recording_duration = request.POST.get('RecordingDuration', None)

    if call_sid:
        CallRecord.objects.filter(twilio_call_sid=call_sid).update(
            recording_url=recording_url,
            recording_sid=recording_sid,
            duration_seconds=int(recording_duration) if recording_duration else None,
            status='completed',
            ended_at=timezone.now(),
        )

    return JsonResponse({'status': 'ok'})


@csrf_exempt
@require_POST
def twilio_status_callback(request):
    """Twilio qo'ng'iroq holati callback."""
    call_sid = request.POST.get('CallSid', '')
    call_status = request.POST.get('CallStatus', '')
    duration = request.POST.get('CallDuration', None)

    status_map = {
        'completed': 'completed',
        'busy': 'missed',
        'no-answer': 'missed',
        'failed': 'failed',
        'canceled': 'missed',
    }

    updates = {
        'status': status_map.get(call_status, 'in_progress'),
        'ended_at': timezone.now() if call_status in status_map else None,
    }
    if duration:
        updates['duration_seconds'] = int(duration)

    CallRecord.objects.filter(twilio_call_sid=call_sid).update(**updates)

    return JsonResponse({'status': 'ok'})


# ── Applications ──────────────────────────────────────────────────────
@login_required
@enrollment_required
def application_list(request):
    status_filter = request.GET.get('status', '')
    grade_filter = request.GET.get('grade', '')

    apps = StudentApplication.objects.select_related('applying_grade', 'lead', 'reviewed_by').all()

    if status_filter:
        apps = apps.filter(status=status_filter)
    if grade_filter:
        apps = apps.filter(applying_grade_id=grade_filter)

    paginator = Paginator(apps, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'grade_filter': grade_filter,
        'status_choices': StudentApplication.APPLICATION_STATUS,
        'grades': Grade.objects.all(),
        'page_title': 'Arizalar',
    }
    return render(request, 'enrollment/application_list.html', context)


@login_required
@enrollment_required
def application_create(request, lead_id=None):
    lead = None
    initial = {}
    if lead_id:
        lead = get_object_or_404(Lead, pk=lead_id)
        initial = {
            'parent_first_name': lead.first_name,
            'parent_last_name': lead.last_name,
            'parent_phone': lead.phone,
            'parent_email': lead.email or '',
            'student_first_name': lead.child_name.split(' ')[0] if lead.child_name else '',
            'student_last_name': ' '.join(lead.child_name.split(' ')[1:]) if lead.child_name else '',
            'applying_grade': lead.interested_grade,
        }

    if request.method == 'POST':
        app = StudentApplication(
            lead=lead,
            parent_first_name=request.POST.get('parent_first_name', '').strip(),
            parent_last_name=request.POST.get('parent_last_name', '').strip(),
            parent_phone=request.POST.get('parent_phone', '').strip(),
            parent_email=request.POST.get('parent_email', '').strip() or None,
            parent_relation=request.POST.get('parent_relation', 'Ota').strip(),
            student_first_name=request.POST.get('student_first_name', '').strip(),
            student_last_name=request.POST.get('student_last_name', '').strip(),
            student_dob=request.POST.get('student_dob') or timezone.now().date(),
            student_gender=request.POST.get('student_gender', 'M'),
            applying_grade_id=request.POST.get('grade') or None,
            previous_school=request.POST.get('previous_school', '').strip(),
            medical_notes=request.POST.get('medical_notes', '').strip(),
            notes=request.POST.get('notes', '').strip(),
            status='submitted',
            submitted_at=timezone.now(),
        )
        app.save()

        if lead:
            lead.status = 'registered'
            lead.save()

        messages.success(request, f'Ariza topshirildi: {app.student_full_name}')
        return redirect('enrollment_application_detail', pk=app.pk)

    context = {
        'lead': lead,
        'initial': initial,
        'grades': Grade.objects.all(),
        'page_title': 'Yangi ariza',
    }
    return render(request, 'enrollment/application_form.html', context)


@login_required
@enrollment_required
def application_detail(request, pk):
    app = get_object_or_404(
        StudentApplication.objects.select_related('applying_grade', 'lead', 'reviewed_by'),
        pk=pk
    )

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update_status':
            app.status = request.POST.get('status', app.status)
            if app.status in ('approved', 'rejected'):
                app.reviewed_by = request.user
                app.reviewed_at = timezone.now()
            app.save()
            messages.success(request, 'Ariza holati yangilandi.')
            return redirect('enrollment_application_detail', pk=app.pk)
        elif action == 'update_notes':
            app.notes = request.POST.get('notes', app.notes)
            app.save()
            messages.success(request, 'Eslatmalar saqlandi.')
            return redirect('enrollment_application_detail', pk=app.pk)

    context = {
        'application': app,
        'status_choices': StudentApplication.APPLICATION_STATUS,
        'page_title': f'Ariza: {app.student_full_name}',
    }
    return render(request, 'enrollment/application_detail.html', context)


# ── Agent profile ─────────────────────────────────────────────────────
@login_required
@enrollment_required
def agent_profile(request):
    agent, _ = AgentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        agent.extension = request.POST.get('extension', agent.extension).strip()
        agent.is_available = request.POST.get('is_available') == 'on'
        agent.save()
        messages.success(request, 'Agent profili yangilandi.')
        return redirect('enrollment_agent_profile')

    context = {
        'agent': agent,
        'page_title': 'Agent profili',
    }
    return render(request, 'enrollment/agent_profile.html', context)


# ── Reports ───────────────────────────────────────────────────────────
@login_required
@enrollment_required
def reports(request):
    # Lead statistics
    leads_by_status = Lead.objects.values('status').annotate(count=Count('id'))
    leads_by_source = Lead.objects.values('source__name').annotate(count=Count('id')).order_by('-count')

    # Call statistics
    calls_completed = CallRecord.objects.filter(status='completed').count()
    total_duration = CallRecord.objects.aggregate(
        total=Sum('duration_seconds')
    )['total'] or 0

    # Application statistics
    apps_by_status = StudentApplication.objects.values('status').annotate(count=Count('id'))
    apps_by_grade = StudentApplication.objects.values('applying_grade__name').annotate(count=Count('id')).order_by('-count')

    context = {
        'leads_by_status': leads_by_status,
        'leads_by_source': leads_by_source,
        'calls_total': CallRecord.objects.count(),
        'calls_completed': calls_completed,
        'calls_missed': CallRecord.objects.filter(status='missed').count(),
        'total_duration': total_duration,
        'applications_by_status': apps_by_status,
        'applications_by_grade': apps_by_grade,
        'page_title': 'Hisobotlar',
    }
    return render(request, 'enrollment/reports.html', context)


# ── API: Twilio token ─────────────────────────────────────────────────
@login_required
@enrollment_required
def twilio_token(request):
    """Brauzerda Twilio Client uchun capability token."""
    from django.conf import settings
    import time
    import hashlib
    import hmac
    import base64

    # Bu yerda Twilio token generatsiya qilinadi.
    # Real production'da twilio-python paketi ishlatiladi:
    # from twilio.jwt.client import ClientCapabilityToken
    # Hozircha placeholder

    agent, _ = AgentProfile.objects.get_or_create(user=request.user)
    agent_identity = f"agent_{request.user.id}"

    # Twilio credentials (environment variables'dan olinadi)
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    api_key = getattr(settings, 'TWILIO_API_KEY', '')
    api_secret = getattr(settings, 'TWILIO_API_SECRET', '')

    if not all([account_sid, api_key, api_secret]):
        return JsonResponse({
            'error': 'Twilio sozlanmagan. Environment variables ni tekshiring.',
            'configured': False,
        }, status=500)

    # Simple token (production'da proper JWT ishlatiladi)
    return JsonResponse({
        'token': f'{account_sid}:{api_key}',
        'identity': agent_identity,
        'configured': True,
    })
