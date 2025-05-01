from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('inventory_manager', 'Inventory Manager'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES)

    class Meta:
        app_label = 'accounts'