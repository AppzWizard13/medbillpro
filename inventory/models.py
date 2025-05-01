from django.db import models
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Medicine(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    price_single = models.DecimalField(max_digits=10, decimal_places=2)
    price_strip = models.DecimalField(max_digits=10, decimal_places=2)
    price_pack = models.DecimalField(max_digits=10, decimal_places=2)
    price_box = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    expiry_date = models.DateField()

    def __str__(self):
        return self.name

    def check_stock_and_expiry(self):
        # Check if stock is low
        if self.stock < 10:  # Example threshold for low stock
            self.send_notification(f'Low stock alert for {self.name}!')

        # Check if medicine is expiring within 30 days
        if (self.expiry_date - timezone.now().date()).days <= 30:
            self.send_notification(f'{self.name} is expiring soon!')

    def send_notification(self, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'notifications',
            {
                'type': 'send_notification',
                'message': message,
            }
        )