# models.py
from django.conf import settings
from django.db import models
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from django.contrib.auth import get_user_model
User = get_user_model()

logger = logging.getLogger(__name__)

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
    stock_threshold = models.IntegerField(default=10)
    expiry_date = models.DateField()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Override save method to check stock after saving
        """
        is_new = self.pk is None
        old_stock = None
        
        if not is_new:
            old_stock = Medicine.objects.get(pk=self.pk).stock
        
        super().save(*args, **kwargs)
        
        # Check stock if it's an update with changed stock or a new creation
        if (not is_new and old_stock != self.stock) or is_new:
            self.check_stock_and_expiry()

    def check_stock_and_expiry(self):
        """
        Check stock and expiry status, send notifications if needed
        """
        logger.info(f"Checking stock for {self.name}: {self.stock} (threshold: {self.stock_threshold})")
        
        # Check for low stock
        if self.stock < self.stock_threshold:
            self.send_notification(
                f'Low stock alert for {self.name}! Current stock: {self.stock} (threshold: {self.stock_threshold})',
                'stock_alert'
            )

        # Check for expiry
        if self._is_expiring_soon():
            self.send_notification(
                f'{self.name} is expiring on {self.expiry_date}!',
                'expiry_alert'
            )

    def _is_expiring_soon(self, days=30):
        """
        Check if medicine expires within given days (default: 30)
        """
        return (self.expiry_date - timezone.now().date()).days <= days

    def send_notification(self, message, category='general'):
        try:
            # Store in database first
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get users who should receive notifications
            users = User.objects.filter(
                models.Q(groups__name__in=['Admin', 'Inventory Manager']) | 
                models.Q(is_superuser=True)
            ).distinct()
            
            # Create notifications for each user
            notifications = [
                Notification(
                    user=user,
                    message=message,
                    category=category,
                    medicine=self
                ) for user in users
            ]
            
            # Bulk create notifications
            Notification.objects.bulk_create(notifications)
            
            # Then send real-time notification
            channel_layer = get_channel_layer()
            print("channel_layerchannel_layer", channel_layer)
            async_to_sync(channel_layer.group_send)(
                'notifications',
                {
                    'type': 'send_notification',
                    'message': message,
                    'category': category,
                    'medicine_id': self.id,
                    'timestamp': str(timezone.now())
                }
            )
            
        except Exception as e:
            logger.error(f"Notification failed: {str(e)}", exc_info=True)

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    category = models.CharField(max_length=20)
    medicine = models.ForeignKey(Medicine, null=True, on_delete=models.SET_NULL)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['created_at']),
        ]