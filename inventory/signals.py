from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Medicine
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Medicine)
def check_stock_and_expiry(sender, instance, **kwargs):
    # Check if stock is low
    if instance.stock < 10:  # Example threshold for low stock
        send_notification(f'Low stock alert for {instance.name}!')

    # Check if medicine is expiring within 30 days
    if (instance.expiry_date - timezone.now().date()).days <= 30:
        send_notification(f'{instance.name} is expiring soon!')

def send_notification(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'notifications',
        {
            'type': 'send_notification',
            'message': message,
        }
    )