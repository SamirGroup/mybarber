"""
ASGI config for bakery_erp project.
WebSocket support for real-time call centre features.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bakery_erp.settings')

django_asgi_app = get_asgi_application()

# Import routing after Django setup
from enrollment import routing as enrollment_routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                enrollment_routing.websocket_urlpatterns
            )
        )
    ),
})
