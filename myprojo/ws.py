import os
import django

# 1️⃣ Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myprojo.settings")  # use your project settings module

# 2️⃣ Initialize Django
django.setup()

# 3️⃣ Now you can safely import Django models or channels
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from submissions_app.models import Submission

# 4️⃣ Example: send a test notification
channel_layer = get_channel_layer()

async_to_sync(channel_layer.group_send)(
    "notifications",
    {
        "type": "send_notification",
        "message": {
            "id": 999,
            "message": "Test notification from ws.py!",
            "submission_id": 1,
            "created_at": "2025-10-04T17:00:00",
        }
    }
)

print("Notification sent!")
