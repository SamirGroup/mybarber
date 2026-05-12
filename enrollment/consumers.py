"""
WebSocket consumers for real-time Call Centre features.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import AgentProfile, CallRecord


class CallCentreConsumer(AsyncWebsocketConsumer):
    """
    Real-time qo'ng'iroq statuslari va bildirishnomalar.
    """
    
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Group'ga qo'shish
        self.room_group_name = 'call_centre'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Ulanish xabari
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to Call Centre'
        }))
    
    async def disconnect(self, close_code):
        # Group'dan chiqarish
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Mijozdan xabar qabul qilish."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': data.get('timestamp')
            }))
        
        elif message_type == 'agent_status_update':
            # Agent statusini yangilash
            status = data.get('status')
            await self.update_agent_status(self.user.id, status)
            
            # Barcha mijozlarga xabar yuborish
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'agent_status_changed',
                    'agent_id': self.user.id,
                    'agent_username': self.user.username,
                    'status': status
                }
            )
    
    async def new_call(self, event):
        """Yangi qo'ng'iroq xabari."""
        await self.send(text_data=json.dumps({
            'type': 'new_call',
            'call_id': event['call_id'],
            'caller_number': event['caller_number'],
            'lead_name': event.get('lead_name', 'Unknown'),
            'assigned_agent': event.get('assigned_agent')
        }))
    
    async def call_status_update(self, event):
        """Qo'ng'iroq status yangilanishi."""
        await self.send(text_data=json.dumps({
            'type': 'call_status_update',
            'call_id': event['call_id'],
            'status': event['status'],
            'duration': event.get('duration')
        }))
    
    async def agent_status_changed(self, event):
        """Agent status o'zgarishi."""
        await self.send(text_data=json.dumps({
            'type': 'agent_status_changed',
            'agent_id': event['agent_id'],
            'agent_username': event['agent_username'],
            'status': event['status']
        }))
    
    @database_sync_to_async
    def update_agent_status(self, user_id, status):
        """Agent statusini yangilash (database)."""
        try:
            agent = AgentProfile.objects.get(user_id=user_id)
            agent.status = status
            agent.is_available = (status == 'online')
            agent.save()
        except AgentProfile.DoesNotExist:
            pass


class AgentStatusConsumer(AsyncWebsocketConsumer):
    """
    Alohida agent uchun status monitoring.
    """
    
    async def connect(self):
        self.agent_id = self.scope['url_route']['kwargs']['agent_id']
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.room_group_name = f'agent_{self.agent_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Agent ma'lumotlarini yuborish
        agent_data = await self.get_agent_data(self.agent_id)
        await self.send(text_data=json.dumps({
            'type': 'agent_data',
            'data': agent_data
        }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'request_stats':
            stats = await self.get_agent_stats(self.agent_id)
            await self.send(text_data=json.dumps({
                'type': 'agent_stats',
                'data': stats
            }))
    
    async def status_update(self, event):
        """Status yangilanishi."""
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': event['status'],
            'timestamp': event['timestamp']
        }))
    
    async def call_assigned(self, event):
        """Yangi qo'ng'iroq tayinlandi."""
        await self.send(text_data=json.dumps({
            'type': 'call_assigned',
            'call_id': event['call_id'],
            'caller_number': event['caller_number'],
            'lead_name': event.get('lead_name')
        }))
    
    @database_sync_to_async
    def get_agent_data(self, agent_id):
        """Agent ma'lumotlarini olish."""
        try:
            agent = AgentProfile.objects.select_related('user').get(user_id=agent_id)
            return {
                'username': agent.user.username,
                'status': agent.status,
                'extension': agent.extension,
                'is_available': agent.is_available,
                'total_calls': agent.total_calls_handled
            }
        except AgentProfile.DoesNotExist:
            return {}
    
    @database_sync_to_async
    def get_agent_stats(self, agent_id):
        """Agent statistikasini olish."""
        from django.utils import timezone
        from django.db.models import Count, Avg
        
        try:
            today = timezone.now().date()
            calls_today = CallRecord.objects.filter(
                agent_id=agent_id,
                created_at__date=today
            )
            
            return {
                'calls_today': calls_today.count(),
                'answered_today': calls_today.filter(status='completed').count(),
                'missed_today': calls_today.filter(status__in=['missed', 'no_answer']).count(),
                'avg_duration': calls_today.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
            }
        except Exception as e:
            return {'error': str(e)}
