from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import submissions_app.routing

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myprojo.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(submissions_app.routing.websocket_urlpatterns)
    ),
})
