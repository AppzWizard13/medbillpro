from django.contrib import admin
from .models import Medicine, Category

# Register custom user model
admin.site.register(Medicine)
admin.site.register(Category)

