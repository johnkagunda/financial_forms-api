import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Notification
from .serializers import NotificationSerializer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "notifications"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send last 20 existing notifications on connect
        notifications = Notification.objects.order_by('-created_at')[:20]
        for notif in notifications:
            await self.send(text_data=json.dumps(NotificationSerializer(notif).data))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    # This handles broadcasted notifications
    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event['message']))
