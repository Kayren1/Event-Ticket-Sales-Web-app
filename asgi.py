import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.events.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paperweight.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # (http->django views is added by default)
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.events.routing.websocket_urlpatterns
        )
    ),
})