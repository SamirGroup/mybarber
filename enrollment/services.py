"""
Call Centre Service Layer
Qo'ng'iroqlarni boshqarish, routing, recording va monitoring uchun biznes logikasi
"""
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.contrib.auth.models import User
from .models import (
    CallRecord, CallQueue, CallRouting, AgentProfile, 
    Lead, AuditLog, CallStatistics
)
import logging

logger = logging.getLogger(__name__)


class CallRoutingService:
    """Qo'ng'iroqlarni operatorlarga yo'naltirish."""
    
    @staticmethod
    def get_available_agents(queue_name='default'):
        """Mavjud operatorlarni olish."""
        return AgentProfile.objects.filter(
            status='online',
            is_available=True,
            user__groups__name='enrollment_agent'
        ).select_related('user')
    
    @staticmethod
    def assign_call_round_robin(call_record):
        """Round-robin algoritmi bilan operator tayinlash."""
        agents = CallRoutingService.get_available_agents()
        
        if not agents.exists():
            logger.warning(f"No available agents for call {call_record.id}")
            return None
        
        # Eng kam qo'ng'iroq qilgan operatorni topish
        agent_stats = {}
        for agent in agents:
            today_calls = CallRecord.objects.filter(
                agent=agent.user,
                created_at__date=timezone.now().date()
            ).count()
            agent_stats[agent] = today_calls
        
        # Eng kam yuklangan operatorni tanlash
        selected_agent = min(agent_stats, key=agent_stats.get)
        
        call_record.agent = selected_agent.user
        call_record.save()
        
        logger.info(f"Call {call_record.id} assigned to agent {selected_agent.user.username}")
        return selected_agent.user
    
    @staticmethod
    def assign_call_least_busy(call_record):
        """Eng kam yuklangan operatorga tayinlash."""
        agents = CallRoutingService.get_available_agents()
        
        if not agents.exists():
            return None
        
        # Hozirda faol qo'ng'iroqlari bo'lgan operatorlarni hisoblash
        agent_loads = {}
        for agent in agents:
            active_calls = CallRecord.objects.filter(
                agent=agent.user,
                status__in=['ringing', 'in_progress']
            ).count()
            agent_loads[agent] = active_calls
        
        # Eng kam yuklangan operatorni tanlash
        selected_agent = min(agent_loads, key=agent_loads.get)
        
        if agent_loads[selected_agent] >= selected_agent.max_concurrent_calls:
            logger.warning(f"All agents are at max capacity")
            return None
        
        call_record.agent = selected_agent.user
        call_record.save()
        
        return selected_agent.user
    
    @staticmethod
    def route_incoming_call(caller_number, routing_config=None):
        """Kiruvchi qo'ng'iroqni yo'naltirish."""
        # Mijozni topish yoki yaratish
        lead = Lead.objects.filter(
            Q(phone=caller_number) | Q(phone_2=caller_number)
        ).first()
        
        if not lead:
            # Yangi lead yaratish
            lead = Lead.objects.create(
                first_name='Yangi',
                last_name='Mijoz',
                phone=caller_number,
                status='new'
            )
            logger.info(f"New lead created for {caller_number}")
        
        # Call record yaratish
        call_record = CallRecord.objects.create(
            lead=lead,
            caller_number=caller_number,
            callee_number=routing_config.phone_number if routing_config else settings.CALL_CENTER_AGENT_NUMBER,
            direction='inbound',
            status='ringing',
            started_at=timezone.now()
        )
        
        # Navbatga qo'shish
        queue_entry = CallQueue.objects.create(
            call=call_record,
            queue_name='default',
            status='waiting'
        )
        
        # Operator tayinlash
        if routing_config:
            if routing_config.strategy == 'round_robin':
                agent = CallRoutingService.assign_call_round_robin(call_record)
            elif routing_config.strategy == 'least_busy':
                agent = CallRoutingService.assign_call_least_busy(call_record)
            else:
                agent = CallRoutingService.assign_call_round_robin(call_record)
        else:
            agent = CallRoutingService.assign_call_round_robin(call_record)
        
        if agent:
            queue_entry.assigned_agent = agent
            queue_entry.status = 'assigned'
            queue_entry.assigned_at = timezone.now()
            queue_entry.save()
        
        return call_record, queue_entry


class RecordingService:
    """Qo'ng'iroqlarni yozib olish xizmati."""
    
    @staticmethod
    def request_recording_consent(call_record):
        """Yozuv uchun rozilik so'rash."""
        call_record.recording_consent = 'pending'
        call_record.save()
        
        # TwiML orqali ovozli xabar yuborish
        consent_message = getattr(
            settings, 
            'CALL_CENTER_CONSENT_TEXT',
            "Salom! Sizning suhbatingiz sifat nazorati uchun yozib olinadi. Rozimisiz? 1 - Ha, 2 - Yo'q"
        )
        
        return consent_message
    
    @staticmethod
    def handle_consent_response(call_record, dtmf_digit):
        """DTMF javobini qayta ishlash."""
        if dtmf_digit == '1':
            call_record.recording_consent = 'accepted'
            call_record.recording_consent_timestamp = timezone.now()
            call_record.save()
            logger.info(f"Recording consent accepted for call {call_record.id}")
            return True
        elif dtmf_digit == '2':
            call_record.recording_consent = 'declined'
            call_record.recording_consent_timestamp = timezone.now()
            call_record.save()
            logger.info(f"Recording consent declined for call {call_record.id}")
            return False
        return None
    
    @staticmethod
    def start_recording(call_record):
        """Yozuvni boshlash."""
        if call_record.recording_consent != 'accepted':
            logger.warning(f"Cannot start recording for call {call_record.id} - no consent")
            return False
        
        # Twilio orqali yozuvni boshlash
        # Bu yerda Twilio API chaqiriladi
        logger.info(f"Recording started for call {call_record.id}")
        return True
    
    @staticmethod
    def save_recording(call_record, recording_url, recording_sid, duration):
        """Yozuvni saqlash."""
        call_record.recording_url = recording_url
        call_record.recording_sid = recording_sid
        call_record.recording_duration = duration
        call_record.save()
        
        # Audit log
        AuditLog.objects.create(
            user=call_record.agent,
            action='recording_started',
            target_model='CallRecord',
            target_id=call_record.id,
            description=f"Recording saved for call {call_record.id}"
        )
        
        logger.info(f"Recording saved for call {call_record.id}")


class CallStatisticsService:
    """Statistika xizmati."""
    
    @staticmethod
    def update_daily_statistics(date=None, agent=None):
        """Kunlik statistikani yangilash."""
        if date is None:
            date = timezone.now().date()
        
        # Agent uchun yoki umumiy statistika
        if agent:
            calls = CallRecord.objects.filter(
                agent=agent,
                created_at__date=date
            )
        else:
            calls = CallRecord.objects.filter(
                created_at__date=date
            )
        
        stats, created = CallStatistics.objects.get_or_create(
            date=date,
            agent=agent,
            defaults={
                'total_calls': 0,
                'inbound_calls': 0,
                'outbound_calls': 0,
                'answered_calls': 0,
                'missed_calls': 0,
            }
        )
        
        # Hisoblash
        stats.total_calls = calls.count()
        stats.inbound_calls = calls.filter(direction='inbound').count()
        stats.outbound_calls = calls.filter(direction='outbound').count()
        stats.answered_calls = calls.filter(status='completed').count()
        stats.missed_calls = calls.filter(status__in=['missed', 'no_answer']).count()
        
        # Vaqt statistikasi
        duration_stats = calls.aggregate(
            total_duration=Sum('duration_seconds'),
            total_talk_time=Sum('talk_time_seconds'),
            total_wait_time=Sum('wait_time_seconds'),
            avg_duration=Avg('duration_seconds'),
            avg_wait_time=Avg('wait_time_seconds')
        )
        
        stats.total_duration_seconds = duration_stats['total_duration'] or 0
        stats.total_talk_time_seconds = duration_stats['total_talk_time'] or 0
        stats.total_wait_time_seconds = duration_stats['total_wait_time'] or 0
        stats.avg_duration_seconds = duration_stats['avg_duration'] or 0
        stats.avg_wait_time_seconds = duration_stats['avg_wait_time'] or 0
        
        # Yozuvlar statistikasi
        stats.recordings_count = calls.exclude(recording_url='').count()
        stats.recordings_with_consent = calls.filter(recording_consent='accepted').count()
        
        stats.save()
        
        logger.info(f"Statistics updated for {date} - Agent: {agent.username if agent else 'All'}")
        return stats
    
    @staticmethod
    def get_agent_performance(agent, start_date=None, end_date=None):
        """Operator samaradorligini olish."""
        if start_date is None:
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        if end_date is None:
            end_date = timezone.now().date()
        
        calls = CallRecord.objects.filter(
            agent=agent,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        performance = {
            'total_calls': calls.count(),
            'answered_calls': calls.filter(status='completed').count(),
            'missed_calls': calls.filter(status__in=['missed', 'no_answer']).count(),
            'avg_duration': calls.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0,
            'total_talk_time': calls.aggregate(Sum('talk_time_seconds'))['talk_time_seconds__sum'] or 0,
            'quality_score': calls.filter(quality_score__isnull=False).aggregate(Avg('quality_score'))['quality_score__avg'] or 0,
        }
        
        # Answer rate
        if performance['total_calls'] > 0:
            performance['answer_rate'] = (performance['answered_calls'] / performance['total_calls']) * 100
        else:
            performance['answer_rate'] = 0
        
        return performance


class AuditService:
    """Audit log xizmati."""
    
    @staticmethod
    def log_action(user, action, target_model=None, target_id=None, description='', request=None):
        """Harakatni loglash."""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        AuditLog.objects.create(
            user=user,
            action=action,
            target_model=target_model,
            target_id=target_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Audit log: {user.username if user else 'System'} - {action}")
    
    @staticmethod
    def get_user_activity(user, days=30):
        """Foydalanuvchi faoliyatini olish."""
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        return AuditLog.objects.filter(
            user=user,
            created_at__gte=start_date
        ).order_by('-created_at')
