import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            if not hasattr(self, 'channel_layer') or not self.channel_layer:
                logger.error("Channel layer not available!")
                raise ValueError("Channel layer not configured")
                
            await self.channel_layer.group_add(
                "notifications",
                self.channel_name
            )
            await self.accept()
        except Exception as e:
            logger.exception("Error in connect:")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'channel_layer') and self.channel_layer:
                await self.channel_layer.group_discard(
                    "notifications",
                    self.channel_name
                )
        except Exception as e:
            logger.exception("Error in disconnect:")

    async def send_notification(self, event):
        try:
            await self.send(text_data=json.dumps({
                "message": event["message"]
            }))
        except Exception as e:
            logger.exception("Error in send_notification:")