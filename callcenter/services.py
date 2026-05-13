import hashlib
import hmac
import json
import logging
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from .models import MetaLead, LeadStatus, LeadStatusHistory, Notification, ApiLog, SystemSettings

logger = logging.getLogger(__name__)


# ── Lead Assignment ───────────────────────────────────────────────────

def get_operator_users():
    return User.objects.filter(
        is_active=True,
        groups__name__in=['callcenter_operator', 'callcenter_supervisor', 'callcenter_admin']
    ).distinct()


def assign_operator_round_robin():
    cfg = SystemSettings.get()
    operators = list(get_operator_users())
    if not operators:
        return None
    idx = cfg.round_robin_index % len(operators)
    operator = operators[idx]
    cfg.round_robin_index = idx + 1
    cfg.save(update_fields=['round_robin_index'])
    return operator


def assign_operator(lead):
    cfg = SystemSettings.get()
    if cfg.assign_mode == 'round_robin':
        return assign_operator_round_robin()
    return None


# ── Meta Graph API ────────────────────────────────────────────────────

def _get_access_token():
    cfg = SystemSettings.get()
    token = cfg.meta_access_token or getattr(settings, 'META_ACCESS_TOKEN', '')
    return token


def fetch_lead_from_meta(lead_id):
    token = _get_access_token()
    version = getattr(settings, 'META_GRAPH_API_VERSION', 'v21.0')
    url = f"https://graph.facebook.com/{version}/{lead_id}?access_token={token}"

    log = ApiLog(api_name='meta_fetch_lead', request_payload={'lead_id': lead_id})
    try:
        resp = requests.get(url, timeout=15)
        log.status_code = resp.status_code
        data = resp.json()
        log.response_payload = data
        log.save()
        if resp.status_code == 200:
            return data
        logger.error(f"Meta fetch lead error: {data}")
        return None
    except Exception as e:
        log.status_code = 0
        log.response_payload = {'error': str(e)}
        log.save()
        logger.exception("Meta fetch lead exception")
        return None


def verify_webhook_signature(request_body: bytes, signature_header: str, app_secret: str) -> bool:
    if not app_secret or not signature_header:
        return True
    expected = 'sha256=' + hmac.new(
        app_secret.encode('utf-8'), request_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def parse_lead_fields(field_data):
    result = {}
    for item in field_data:
        result[item.get('name', '')] = item.get('values', [''])[0]
    return result


def process_meta_lead(lead_id, page_id=None, form_id=None, raw_payload=None):
    # Duplicate check
    if MetaLead.objects.filter(lead_uuid=str(lead_id)).exists():
        logger.info(f"Duplicate lead ignored: {lead_id}")
        return None, 'duplicate'

    data = fetch_lead_from_meta(lead_id)
    if not data:
        return None, 'fetch_failed'

    field_map = parse_lead_fields(data.get('field_data', []))

    phone = ''
    for f in ['phone_number', 'phone', 'mobile_number']:
        if field_map.get(f):
            phone = field_map[f]
            break

    full_name = field_map.get('full_name') or field_map.get('first_name', '') + ' ' + field_map.get('last_name', '')
    full_name = full_name.strip() or 'Noma\'lum'

    status_new = LeadStatus.objects.filter(code='new').first()

    lead = MetaLead(
        lead_uuid=str(lead_id),
        full_name=full_name,
        phone_number=phone,
        phone_number2=field_map.get('phone_number_2', ''),
        region=field_map.get('region', ''),
        product_interest=field_map.get('product_interest', ''),
        campaign_name=data.get('ad_name', ''),
        adset_name=data.get('adset_name', ''),
        form_name=data.get('form_id', form_id or ''),
        meta_created_time=data.get('created_time'),
        current_status=status_new,
        raw_payload=raw_payload,
    )

    operator = assign_operator(lead)
    lead.assigned_operator = operator
    lead.save()

    LeadStatusHistory.objects.create(
        lead=lead,
        new_status=status_new,
        comment='Meta webhook orqali avtomatik yaratildi',
    )

    _notify_new_lead(lead, operator)
    return lead, 'created'


def _notify_new_lead(lead, operator):
    admins = User.objects.filter(is_superuser=True)
    text = f"Yangi lead: {lead.full_name} ({lead.phone_number})"
    for admin in admins:
        Notification.objects.create(
            user=admin, lead=lead,
            notification_text=text,
            notification_type='new_lead'
        )
    if operator:
        Notification.objects.create(
            user=operator, lead=lead,
            notification_text=f"Sizga yangi lead biriktirildi: {lead.full_name}",
            notification_type='new_lead'
        )


# ── Simulated lead for testing (no real Meta API needed) ──────────────

def create_test_lead(full_name, phone, region='', product_interest='', campaign='Test Campaign'):
    status_new = LeadStatus.objects.filter(code='new').first()
    import uuid
    lead = MetaLead(
        lead_uuid=str(uuid.uuid4()),
        full_name=full_name,
        phone_number=phone,
        region=region,
        product_interest=product_interest,
        campaign_name=campaign,
        current_status=status_new,
        raw_payload={'source': 'manual_test'},
    )
    operator = assign_operator(lead)
    lead.assigned_operator = operator
    lead.save()

    LeadStatusHistory.objects.create(
        lead=lead,
        new_status=status_new,
        comment='Test lead yaratildi',
    )
    _notify_new_lead(lead, operator)
    return lead
