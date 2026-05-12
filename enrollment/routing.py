"""
WebSocket routing for Call Centre real-time features.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/call-centre/$', consumers.CallCentreConsumer.as_asgi()),
    re_path(r'ws/call-centre/agent/(?P<agent_id>\w+)/$', consumers.AgentStatusConsumer.as_asgi()),
]
