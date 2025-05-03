# consumers.py
import json
import logging
import os
import django
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

# Django setup must happen after imports but before any Django code
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medbillpro.settings')
django.setup()

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Get token from query string more efficiently
            query_params = self.scope.get('query_string', b'').decode()
            token = None

            # More robust token extraction
            token = next(
                (param.split('=')[1] for param in query_params.split('&')
                 if param.startswith('token=')),
                None
            )

            if not token:
                logger.error("No token provided in connection request")
                await self.close(code=4001)  # Unauthorized status code
                return

            # Authenticate user
            user = await self.get_user_from_token(token)
            if user is None:
                await self.close(code=4001)
                return

            # Check authorization
            is_authorized = await self.check_user_authorization(user)
            if not is_authorized:
                await self.close(code=4003)  # Forbidden status code
                return

            # Store user and add to groups
            self.user = user
            self.group_name = f'user_{user.id}_notifications'

            # Add to both global notifications group and user-specific group
            await self.channel_layer.group_add(
                "notifications",
                self.channel_name
            )
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()
            logger.info(f"WebSocket connected for {user.username}")

        except Exception as e:
            logger.exception(f"Error in connect: {str(e)}")
            await self.close(code=4000)  # Generic error code

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection with group cleanup."""
        # Clean up groups on disconnect
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                "notifications",
                self.channel_name
            )
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        logger.info(
            "WebSocket disconnected for "
            f"{getattr(self, 'user', 'unknown')}"
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'mark_as_read':
                await self.mark_notification_as_read(
                    data.get('notification_id')
                )
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    async def send_notification(self, event):
        """Handle 'send_notification' events from the channel layer."""
        try:
            await self.send(text_data=json.dumps({
                'type': event['category'],
                'message': event['message'],
                'medicine_id': event['medicine_id'],
                'timestamp': event['timestamp'],
                'notification_id': event.get('notification_id')
            }))
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")

    @database_sync_to_async
    def get_user_from_token(self, token):
        """Get user from JWT token."""
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth import get_user_model

            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return get_user_model().objects.get(id=user_id)
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return None

    @database_sync_to_async
    def check_user_authorization(self, user):
        """Check if user is authorized to receive notifications."""
        return (
            user.groups.filter(
                name__in=['Admin', 'Inventory Manager']
            ).exists() or user.is_superuser
        )

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Mark a notification as read."""
        try:
            from inventory.models import Notification
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            logger.error(
                "Notification %s not found for user %s",
                notification_id,
                self.user
            )
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False
