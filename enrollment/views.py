from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import (
    Lead, LeadSource, Grade, AcademicYear, CallRecord,
    CallCampaign, StudentApplication, AgentProfile, LeadComment, LeadStatusHistory,
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
    comments = lead.comments.select_related('user').order_by('-created_at')
    status_history = lead.status_history.select_related('changed_by').order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update_status':
            old_status = lead.status
            lead.status = request.POST.get('status', lead.status)
            status_note = request.POST.get('status_note', '').strip()
            if lead.status == 'contacted' and not lead.contacted_at:
                lead.contacted_at = timezone.now()
            lead._changed_by = request.user
            lead.save()
            
            # Status o'zgarganda izoh qo'shish
            if status_note:
                LeadComment.objects.create(
                    lead=lead,
                    user=request.user,
                    comment=status_note
                )
            
            messages.success(request, 'Lead holati yangilandi.')
            return redirect('enrollment_lead_detail', pk=lead.pk)
        elif action == 'add_comment':
            comment_text = request.POST.get('comment', '').strip()
            if comment_text:
                LeadComment.objects.create(
                    lead=lead,
                    user=request.user,
                    comment=comment_text
                )
                messages.success(request, 'Izoh qo\'shildi.')
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
        'comments': comments,
        'status_history': status_history,
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
def meta_lead_webhook(request):
    """Meta (Facebook/Instagram) dan lead'larni qabul qiluvchi webhook."""
    # GET request - webhook verification
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        verify_token = getattr(settings, 'META_VERIFY_TOKEN', 'bunyod_school_2025')
        
        if mode == 'subscribe' and token == verify_token:
            return HttpResponse(challenge, content_type='text/plain')
        return HttpResponse('Verification failed', status=403)
    
    # POST request - lead data
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    entries = data.get('entry', [])
    created = 0
    
    for entry in entries:
        changes = entry.get('changes', [])
        for change in changes:
            field = change.get('field')
            if field != 'leadgen':
                continue
                
            value = change.get('value', {})
            leadgen_id = value.get('leadgen_id', '')
            form_id = value.get('form_id', '')
            page_id = value.get('page_id', '')
            adgroup_id = value.get('adgroup_id', '')
            ad_id = value.get('ad_id', '')
            created_time = value.get('created_time', '')
            
            # Meta Lead Source yaratish
            lead_source, _ = LeadSource.objects.get_or_create(
                code='meta',
                defaults={'name': 'Meta (Facebook/Instagram)'}
            )
            
            # Agar META_LEAD_FETCH_ENABLED=True bo'lsa, Graph API orqali to'liq ma'lumot olish
            field_data = {}
            if getattr(settings, 'META_LEAD_FETCH_ENABLED', False) and leadgen_id:
                try:
                    import requests
                    access_token = getattr(settings, 'META_ACCESS_TOKEN', '')
                    graph_version = getattr(settings, 'META_GRAPH_API_VERSION', 'v21.0')
                    url = f'https://graph.facebook.com/{graph_version}/{leadgen_id}'
                    params = {'access_token': access_token}
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        lead_data = response.json()
                        field_data = {item['name']: item['values'][0] for item in lead_data.get('field_data', [])}
                except Exception as e:
                    print(f'Meta Graph API error: {e}')
            
            # Field mapping
            phone_fields = getattr(settings, 'META_LEAD_MAP_PHONE_FIELDS', ['phone_number', 'phone', 'mobile_number'])
            email_fields = getattr(settings, 'META_LEAD_MAP_EMAIL_FIELDS', ['email'])
            first_name_fields = getattr(settings, 'META_LEAD_MAP_PARENT_FIRST_FIELDS', ['first_name', 'full_name'])
            last_name_fields = getattr(settings, 'META_LEAD_MAP_PARENT_LAST_FIELDS', ['last_name'])
            child_name_fields = getattr(settings, 'META_LEAD_MAP_CHILD_NAME_FIELDS', ['child_name', 'student_name'])
            grade_fields = getattr(settings, 'META_LEAD_MAP_GRADE_FIELDS', ['grade', 'class'])
            region_fields = ['region', 'city', 'viloyat']
            phone_2_fields = ['phone_2', 'additional_phone', 'qoshimcha_telefon']
            children_count_fields = ['children_count', 'bolalar_soni', 'number_of_children']
            
            # Extract data
            phone = ''
            for field in phone_fields:
                if field in field_data:
                    phone = field_data[field]
                    break
            
            phone_2 = ''
            for field in phone_2_fields:
                if field in field_data:
                    phone_2 = field_data[field]
                    break
            
            email = ''
            for field in email_fields:
                if field in field_data:
                    email = field_data[field]
                    break
            
            first_name = ''
            for field in first_name_fields:
                if field in field_data:
                    first_name = field_data[field]
                    break
            
            last_name = ''
            for field in last_name_fields:
                if field in field_data:
                    last_name = field_data[field]
                    break
            
            # Agar full_name bo'lsa, ajratish
            if not last_name and first_name and ' ' in first_name:
                parts = first_name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
            
            child_name = ''
            for field in child_name_fields:
                if field in field_data:
                    child_name = field_data[field]
                    break
            
            grade_name = ''
            for field in grade_fields:
                if field in field_data:
                    grade_name = field_data[field]
                    break
            
            region = ''
            for field in region_fields:
                if field in field_data:
                    region = field_data[field]
                    break
            
            children_count = 1
            for field in children_count_fields:
                if field in field_data:
                    try:
                        children_count = int(field_data[field])
                    except:
                        children_count = 1
                    break
            
            # Telefon normalizatsiya
            if phone and not phone.startswith('+'):
                if phone.startswith('998'):
                    phone = '+' + phone
                elif len(phone) == 9:
                    phone = '+998' + phone
            
            if phone_2 and not phone_2.startswith('+'):
                if phone_2.startswith('998'):
                    phone_2 = '+' + phone_2
                elif len(phone_2) == 9:
                    phone_2 = '+998' + phone_2
            
            # Telefon majburiy
            if not phone:
                continue
            
            # Grade topish
            grade = None
            if grade_name:
                grade = Grade.objects.filter(name__icontains=grade_name).first()
            
            # Chegirma hisoblash
            discount_info = "Chegirma yo'q"
            if children_count >= 3:
                discount_info = "20% chegirma (3+ bola)"
            elif children_count >= 2:
                discount_info = "10% chegirma (2+ bola)"
            
            # Campaign ma'lumotlari
            campaign_name = field_data.get('campaign_name', 'New Academic Year')
            adset_name = field_data.get('adset_name', 'Parents 25-45')
            form_name = field_data.get('form_name', 'Open Day RSVP')
            
            # Dublikat tekshirish
            existing = Lead.objects.filter(
                phone=phone,
                created_at__gte=timezone.now() - timezone.timedelta(
                    minutes=getattr(settings, 'META_LEAD_DUPLICATE_WINDOW_MINUTES', 60)
                )
            ).first()
            
            if existing:
                # Dublikat, yangilaymiz
                existing.meta_campaign_name = campaign_name
                existing.meta_adset_name = adset_name
                existing.meta_form_name = form_name
                existing.save()
                continue
            
            # Yangi lead yaratish
            lead = Lead.objects.create(
                first_name=first_name or 'Lead',
                last_name=last_name or 'Parent',
                phone=phone,
                phone_2=phone_2,
                email=email or None,
                region=region,
                child_name=child_name,
                children_count=children_count,
                interested_grade=grade,
                discount_info=discount_info,
                source=lead_source,
                meta_lead_id=leadgen_id,
                meta_campaign_name=campaign_name,
                meta_adset_name=adset_name,
                meta_form_name=form_name,
                meta_campaign_id=str(adgroup_id) if adgroup_id else '',
                meta_ad_id=str(ad_id) if ad_id else '',
                meta_form_id=str(form_id) if form_id else '',
                status='new',
                notes=f"Parent inquired about enrollment for {children_count} child(ren) in {grade_name or 'N/A'}.",
            )
            
            # Auto-assign first available agent
            if getattr(settings, 'META_LEAD_AUTO_ASSIGN_FIRST_AGENT', True):
                agent = User.objects.filter(
                    groups__name='enrollment_agent',
                    agent_profile__is_available=True
                ).first()
                if agent:
                    lead.assigned_to = agent
                    lead.save()
            
            created += 1

    return JsonResponse({'status': 'ok', 'created': created})


# ── Call Centre ───────────────────────────────────────────────────────
@login_required
@enrollment_required
def call_centre(request):
    """Call centre interfeysi — brauzer ichida IP telefoniya (Twilio asosida)."""
    agent, _ = AgentProfile.objects.get_or_create(user=request.user)

    # Handle agent availability toggle
    if request.method == 'POST':
        agent.is_available = request.POST.get('is_available') == 'on'
        agent.save()
        messages.success(request, 'Agent holati yangilandi')
        return redirect('enrollment_call_centre')

    recent_calls = CallRecord.objects.select_related('lead', 'agent').filter(
        agent=request.user
    ).order_by('-created_at')[:20]

    active_calls = CallRecord.objects.select_related('lead').filter(
        agent=request.user, status__in=['ringing', 'in_progress']
    )

    # For quick dial
    recent_leads = Lead.objects.filter(
        status__in=['new', 'contacted', 'interested']
    ).order_by('-created_at')[:20]

    context = {
        'agent': agent,
        'recent_calls': recent_calls,
        'active_calls': active_calls,
        'recent_leads': recent_leads,
        'page_title': 'Call Centre',
    }
    return render(request, 'enrollment/call_centre/call_panel.html', context)


@login_required
@enrollment_required
def call_initiate(request):
    """Yangi qo'ng'iroq boshlash — Twilio yoki local mode (demo)."""
    if request.method == 'POST':
        to_number = request.POST.get('to_number', '').strip()
        lead_id = request.POST.get('lead_id', None)

        if not to_number:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Telefon raqam kiritilishi kerak.'}, status=400)
            messages.error(request, 'Telefon raqam kiritilishi kerak.')
            return redirect('enrollment_call_centre')

        # Normalize phone number for Uzbekistan
        if not to_number.startswith('+'):
            if to_number.startswith('998'):
                to_number = '+' + to_number
            elif len(to_number) == 9:
                to_number = '+998' + to_number

        lead = None
        if lead_id:
            try:
                lead = get_object_or_404(Lead, pk=lead_id)
            except Exception:
                lead = None

        # Get agent's phone number
        agent_number = getattr(settings, 'CALL_CENTER_AGENT_NUMBER', '+998901234567')

        # Create call record — always works even without Twilio
        call = CallRecord.objects.create(
            lead=lead,
            agent=request.user,
            caller_number=agent_number,
            callee_number=to_number,
            direction='outbound',
            status='in_progress',
            started_at=timezone.now(),
        )

        # Twilio integration (only if configured)
        call_sid = None
        twilio_configured = all([
            getattr(settings, 'TWILIO_ACCOUNT_SID', ''),
            getattr(settings, 'TWILIO_AUTH_TOKEN', ''),
        ])

        if twilio_configured:
            try:
                from twilio.rest import Client
                twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
                twilio_call = twilio_client.calls.create(
                    to=to_number,
                    from_=agent_number,
                    url=request.build_absolute_uri('/enrollment/twilio/voice/'),
                    status_callback=request.build_absolute_uri('/enrollment/twilio/status-callback/'),
                    status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                    record=True,
                    recording_status_callback=request.build_absolute_uri('/enrollment/twilio/recording-status/'),
                )
                call.twilio_call_sid = twilio_call.sid
                call.save()
                call_sid = twilio_call.sid
            except Exception as e:
                print(f'Twilio error: {e}')
                # Continue with local call even if Twilio fails

        # Simulate call completion for demo (in production, this happens via status callback)
        # For demo/testing, mark as completed after 30 seconds if no Twilio SID
        if not call_sid:
            # Local demo mode - simulate immediate connection
            call.status = 'in_progress'
            call.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'ok',
                'call_sid': call_sid or f'local_{call.id}',
                'call_id': call.id,
                'to_number': to_number,
                'demo_mode': not twilio_configured,
            })

        messages.success(request, f'Qo\'ng\'iroq {to_number} raqamiga yo\'naltirildi.')
        return redirect('enrollment_call_centre')

    leads = Lead.objects.filter(status__in=['new', 'contacted', 'interested']).order_by('-created_at')[:50]
    context = {
        'leads': leads,
        'page_title': 'Qo\'ng\'iroq qilish',
    }
    return render(request, 'enrollment/call_initiate.html', context)


@login_required
@enrollment_required
@require_POST
def call_end(request):
    """Qo'ng'iroqni tugatish."""
    call_sid = request.POST.get('call_sid', '')
    
    if call_sid:
        if call_sid.startswith('local_'):
            # Local demo mode - find by call ID
            try:
                call_id = int(call_sid.split('_')[1])
                CallRecord.objects.filter(id=call_id).update(
                    status='completed',
                    ended_at=timezone.now(),
                )
            except (ValueError, IndexError):
                pass
        else:
            # Twilio call end
            try:
                from twilio.rest import Client
                twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                twilio_call = twilio_client.calls(call_sid)
                twilio_call.update(status='completed')
            except Exception as e:
                print(f'Twilio end call error: {e}')
            
            CallRecord.objects.filter(twilio_call_sid=call_sid).update(
                status='completed',
                ended_at=timezone.now(),
            )
    
    return JsonResponse({'status': 'ok'})


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
    # O'zbekiston kompaniyalari uchun so'zlar
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="uz-UZ">Xususiy Maktab qabul bo'limiga xush kelibsiz. Iltimos, kuting, operator siz bilan bog'lanadi.</Say>
    <Dial record="record-from-ringing-dual" 
          recordingStatusCallback="/enrollment/twilio/recording-status/"
          recordingStatusCallbackMethod="POST">
        <Number>{getattr(settings, 'CALL_CENTER_AGENT_NUMBER', '+998901234567')}</Number>
    </Dial>
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


# ── API Endpoints (JSON responses) ─────────────────────────────────────
@login_required
@enrollment_required
def api_customer_info(request):
    """Mijoz ma'lumotlarini olish (telefon raqam bo'yicha)."""
    phone = request.GET.get('phone', '').strip()
    
    if not phone:
        return JsonResponse({'found': False, 'error': 'Phone number required'})
    
    # Telefon raqamni normalizatsiya qilish
    phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Lead qidirish
    lead = Lead.objects.filter(
        Q(phone__icontains=phone_clean) | Q(phone_2__icontains=phone_clean)
    ).select_related('interested_grade', 'source').first()
    
    if not lead:
        return JsonResponse({'found': False})
    
    # Oxirgi qo'ng'iroq
    last_call = CallRecord.objects.filter(lead=lead).order_by('-created_at').first()
    
    return JsonResponse({
        'found': True,
        'id': lead.id,
        'name': lead.full_name,
        'phone': lead.phone,
        'phone_2': lead.phone_2,
        'email': lead.email or '',
        'region': lead.region or '',
        'children_count': lead.children_count,
        'interested_grade': lead.interested_grade.name if lead.interested_grade else '',
        'status': lead.get_status_display(),
        'source': lead.source.name if lead.source else '',
        'last_call': last_call.created_at.strftime('%d.%m.%Y %H:%M') if last_call else 'Hech qachon',
        'notes': lead.notes,
    })


@login_required
@enrollment_required
def api_agent_stats(request):
    """Agent statistikasini olish (bugungi kun)."""
    from django.db.models import Avg
    today = timezone.now().date()
    
    calls_today = CallRecord.objects.filter(
        agent=request.user,
        created_at__date=today
    )
    
    stats = {
        'calls_today': calls_today.count(),
        'answered_today': calls_today.filter(status='completed').count(),
        'missed_today': calls_today.filter(status__in=['missed', 'no_answer']).count(),
        'inbound_today': calls_today.filter(direction='inbound').count(),
        'outbound_today': calls_today.filter(direction='outbound').count(),
        'avg_duration': int(calls_today.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0),
        'total_talk_time': int(calls_today.aggregate(Sum('talk_time_seconds'))['talk_time_seconds__sum'] or 0),
    }
    
    return JsonResponse(stats)


@login_required
@enrollment_required
def api_call_queue(request):
    """Navbatdagi qo'ng'iroqlarni olish."""
    from .models import CallQueue
    
    queue = CallQueue.objects.filter(
        status='waiting'
    ).select_related('call', 'call__lead').order_by('-priority', 'entered_at')[:10]
    
    queue_data = []
    for entry in queue:
        queue_data.append({
            'id': entry.id,
            'caller_number': entry.call.caller_number,
            'lead_name': entry.call.lead.full_name if entry.call.lead else 'Noma\'lum',
            'wait_time': entry.wait_time_seconds,
            'position': entry.position,
        })
    
    return JsonResponse({'queue': queue_data})


@login_required
@enrollment_required
def agent_status_update(request):
    """Agent statusini yangilash."""
    if request.method == 'POST':
        status = request.POST.get('status', 'offline')
        
        agent, _ = AgentProfile.objects.get_or_create(user=request.user)
        agent.status = status
        agent.is_available = (status == 'online')
        agent.save()
        
        # Audit log
        from .services import AuditService
        AuditService.log_action(
            user=request.user,
            action='agent_status_changed',
            description=f"Status changed to {status}",
            request=request
        )
        
        return JsonResponse({'status': 'ok', 'new_status': status})
    
    return JsonResponse({'error': 'POST required'}, status=400)


@login_required
@enrollment_required
def call_notes_update(request, call_id):
    """Qo'ng'iroq eslatmasini yangilash."""
    if request.method == 'POST':
        call = get_object_or_404(CallRecord, id=call_id, agent=request.user)
        notes = request.POST.get('notes', '').strip()
        
        call.notes = notes
        call.save()
        
        return JsonResponse({'status': 'ok'})
    
    return JsonResponse({'error': 'POST required'}, status=400)


@csrf_exempt
@require_POST
def sip_webhook(request):
    """O'zbekiston SIP provider'lari uchun webhook (Ucell, Beeline, Umnitel)"""
    from django.conf import settings
    
    # SIP call ma'lumotlari
    call_sid = request.POST.get('CallSid', '')
    caller = request.POST.get('From', '')
    callee = request.POST.get('To', '')
    direction = request.POST.get('Direction', 'inbound')
    status = request.POST.get('CallStatus', '')
    
    # Call record yaratish/yangilash
    call_record, created = CallRecord.objects.update_or_create(
        twilio_call_sid=call_sid,
        defaults={
            'caller_number': caller,
            'callee_number': callee,
            'direction': direction,
            'status': status,
            'started_at': timezone.now(),
        }
    )
    
    # O'zbekiston operatorlari uchun log
    if call_record.is_uzbekistan_number(caller):
        operator = call_record.get_operator(caller)
        print(f"[SIP Webhook] Qo'ng'iroq: {caller} ({operator}) → {callee}")
    
    return JsonResponse({'status': 'ok'})
