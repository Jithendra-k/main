from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack

import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class AdminNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            if not self.scope["user"].is_staff:
                await self.close()
                return

            await self.channel_layer.group_add("admin_notifications", self.channel_name)
            await self.accept()
            logger.info(f"WebSocket connected for user {self.scope['user']}")
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard("admin_notifications", self.channel_name)
            logger.info(f"WebSocket disconnected for user {self.scope['user']}")
        except Exception as e:
            logger.error(f"WebSocket disconnect error: {str(e)}")

    async def notification_message(self, event):
        try:
            message = event['message']
            await self.send(text_data=json.dumps(message))
            logger.info(f"Message sent successfully: {message['type']}")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")