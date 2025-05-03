from django.db import models
from inventory.models import Medicine
from django.contrib.auth import get_user_model
User = get_user_model()
import random
import string

class Bill(models.Model):
    staff_user = models.ForeignKey(User, on_delete=models.PROTECT)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    billing_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)  # Unique field for invoice number

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate a unique invoice number (customize the format as needed)
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        # This method generates a random invoice number with a prefix and a sequential number
        prefix = "INV-"
        # You could use the ID or another logic for sequential numbering
        unique_number = ''.join(random.choices(string.digits, k=6))  # Random 6 digit number
        return f"{prefix}{unique_number}"


class BillItem(models.Model):
    PACKAGING_TYPES = [
        ('single', 'Single Unit'),
        ('strip', 'Strip'),
        ('pack', 'Pack'),
        ('box', 'Box'),
    ]
    
    bill = models.ForeignKey(Bill, related_name='items', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    packaging_type = models.CharField(max_length=10, choices=PACKAGING_TYPES)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)