from django.contrib import admin
from .models import Bill

# Register custom user model
admin.site.register(Bill)

