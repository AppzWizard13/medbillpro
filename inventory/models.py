from django.db import models
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = "Categories"


class Medicine(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='medicines')
    price_single = models.DecimalField(max_digits=10, decimal_places=2)
    price_strip = models.DecimalField(max_digits=10, decimal_places=2)
    price_pack = models.DecimalField(max_digits=10, decimal_places=2)
    price_box = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    stock_threshold = models.IntegerField(default=10)  # New field for threshold
    expiry_date = models.DateField()

    def __str__(self):
        return self.name

    def check_stock_and_expiry(self):
        """Check stock and expiry status, send notifications if needed"""
        if self.stock < self.stock_threshold:  # Now using threshold field
            self.send_notification(f'Low stock alert for {self.name}! Current stock: {self.stock} (threshold: {self.stock_threshold})')

        if self._is_expiring_soon():
            self.send_notification(f'{self.name} is expiring on {self.expiry_date}!')

    def _is_expiring_soon(self, days=30):
        """Check if medicine expires within given days (default: 30)"""
        return (self.expiry_date - timezone.now().date()).days <= days

    def send_notification(self, message):
        """Send notification through Django Channels"""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'notifications',
            {
                'type': 'send_notification',
                'message': message,
            }
        )
