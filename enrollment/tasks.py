"""
Celery tasks for Call Centre background processing.
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from .models import CallRecord, CallStatistics, AgentProfile
from .services import CallStatisticsService
import logging
import os

logger = logging.getLogger(__name__)


@shared_task
def update_daily_statistics():
    """Kunlik statistikani yangilash."""
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    
    # Umumiy statistika
    CallStatisticsService.update_daily_statistics(date=yesterday, agent=None)
    
    # Har bir agent uchun
    agents = User.objects.filter(groups__name='enrollment_agent')
    for agent in agents:
        CallStatisticsService.update_daily_statistics(date=yesterday, agent=agent)
    
    logger.info(f"Daily statistics updated for {yesterday}")
    return f"Updated statistics for {yesterday}"


@shared_task
def cleanup_old_recordings():
    """Eski yozuvlarni tozalash."""
    retention_days = getattr(settings, 'CALL_CENTER_KEEP_RECORDING_DAYS', 365)
    cutoff_date = timezone.now() - timezone.timedelta(days=retention_days)
    
    old_recordings = CallRecord.objects.filter(
        created_at__lt=cutoff_date,
        recording_file__isnull=False
    )
    
    deleted_count = 0
    for call in old_recordings:
        if call.recording_file:
            # Faylni o'chirish
            if os.path.exists(call.recording_file.path):
                os.remove(call.recording_file.path)
            call.recording_file = None
            call.save()
            deleted_count += 1
    
    logger.info(f"Cleaned up {deleted_count} old recordings")
    return f"Deleted {deleted_count} recordings older than {retention_days} days"


@shared_task
def check_abandoned_calls():
    """Tashlab ketilgan qo'ng'iroqlarni tekshirish."""
    from .models import CallQueue
    
    max_wait = getattr(settings, 'CALL_QUEUE_MAX_WAIT_SECONDS', 300)
    cutoff_time = timezone.now() - timezone.timedelta(seconds=max_wait)
    
    abandoned = CallQueue.objects.filter(
        status='waiting',
        entered_at__lt=cutoff_time
    )
    
    count = 0
    for queue_entry in abandoned:
        queue_entry.status = 'abandoned'
        queue_entry.left_at = timezone.now()
        queue_entry.save()
        
        # Call record yangilash
        if queue_entry.call:
            queue_entry.call.status = 'missed'
            queue_entry.call.ended_at = timezone.now()
            queue_entry.call.save()
        
        count += 1
    
    logger.info(f"Marked {count} calls as abandoned")
    return f"Processed {count} abandoned calls"


@shared_task
def download_twilio_recording(call_id, recording_url):
    """Twilio'dan yozuvni yuklab olish."""
    import requests
    from django.core.files.base import ContentFile
    
    try:
        call = CallRecord.objects.get(id=call_id)
        
        # Twilio'dan yuklab olish
        response = requests.get(recording_url, timeout=30)
        if response.status_code == 200:
            # Faylni saqlash
            filename = f"call_{call_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            call.recording_file.save(filename, ContentFile(response.content))
            call.save()
            
            logger.info(f"Downloaded recording for call {call_id}")
            return f"Recording downloaded for call {call_id}"
        else:
            logger.error(f"Failed to download recording for call {call_id}: {response.status_code}")
            return f"Failed: {response.status_code}"
    
    except CallRecord.DoesNotExist:
        logger.error(f"Call {call_id} not found")
        return f"Call {call_id} not found"
    except Exception as e:
        logger.error(f"Error downloading recording for call {call_id}: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_call_notification(agent_id, call_id, caller_number):
    """Operatorga qo'ng'iroq haqida bildirishnoma yuborish."""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    try:
        agent = User.objects.get(id=agent_id)
        call = CallRecord.objects.get(id=call_id)
        
        channel_layer = get_channel_layer()
        
        # WebSocket orqali xabar yuborish
        async_to_sync(channel_layer.group_send)(
            f'agent_{agent_id}',
            {
                'type': 'call_assigned',
                'call_id': call_id,
                'caller_number': caller_number,
                'lead_name': call.lead.full_name if call.lead else 'Unknown'
            }
        )
        
        logger.info(f"Notification sent to agent {agent.username} for call {call_id}")
        return f"Notification sent to {agent.username}"
    
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def generate_agent_report(agent_id, start_date, end_date):
    """Operator uchun hisobot yaratish."""
    from django.core.mail import send_mail
    
    try:
        agent = User.objects.get(id=agent_id)
        performance = CallStatisticsService.get_agent_performance(
            agent, start_date, end_date
        )
        
        # Email yuborish (agar sozlangan bo'lsa)
        if agent.email:
            subject = f"Call Centre Report - {start_date} to {end_date}"
            message = f"""
            Agent: {agent.username}
            Period: {start_date} to {end_date}
            
            Total Calls: {performance['total_calls']}
            Answered: {performance['answered_calls']}
            Missed: {performance['missed_calls']}
            Answer Rate: {performance['answer_rate']:.1f}%
            Avg Duration: {performance['avg_duration']:.0f} seconds
            Quality Score: {performance['quality_score']:.1f}/5
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [agent.email],
                fail_silently=True
            )
        
        logger.info(f"Report generated for agent {agent.username}")
        return f"Report generated for {agent.username}"
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def update_agent_status_offline():
    """Uzoq vaqt faol bo'lmagan operatorlarni offline qilish."""
    timeout_minutes = 30
    cutoff_time = timezone.now() - timezone.timedelta(minutes=timeout_minutes)
    
    inactive_agents = AgentProfile.objects.filter(
        status='online',
        updated_at__lt=cutoff_time
    )
    
    count = 0
    for agent in inactive_agents:
        agent.status = 'offline'
        agent.is_available = False
        agent.save()
        count += 1
    
    logger.info(f"Set {count} agents to offline due to inactivity")
    return f"Updated {count} agents to offline"
