from rest_framework import serializers
from .models import Bill, BillItem
from django.contrib.auth import get_user_model
User = get_user_model()

class BillItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    packaging_type = serializers.ChoiceField(choices=BillItem.PACKAGING_TYPES)
    
    class Meta:
        model = BillItem
        fields = [
            'medicine_name',
            'quantity',
            'packaging_type',
            'unit_price',
            'total_price'
        ]

class BillSerializer(serializers.ModelSerializer):
    staff_user_username = serializers.CharField(source='staff_user.username', read_only=True)
    items = BillItemSerializer(many=True, required=False)  # Set required=False here
    staff_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)  # Explicitly handle staff_user as a FK to User
    
    class Meta:
        model = Bill
        fields = [
            'staff_user_username',
            'customer_name',
            'customer_email',
            'customer_phone',
            'billing_address',
            'total_amount',
            'created_at',
            'items',
            'staff_user',
            'invoice_number'
        ]
