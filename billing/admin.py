from django.contrib import admin
from .models import Bill, BillItem

# Register custom user model
admin.site.register(Bill)
admin.site.register(BillItem)

