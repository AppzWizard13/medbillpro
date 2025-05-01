from rest_framework import serializers
from .models import Medicine

class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': False},
            'category': {'required': False},
            'price_single': {'required': False},
            'price_strip': {'required': False},
            'price_pack': {'required': False},
            'price_box': {'required': False},
            'stock': {'required': False},
            'expiry_date': {'required': False},
        }
