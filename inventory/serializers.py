from rest_framework import serializers
from .models import Medicine, Category

class MedicineSerializer(serializers.ModelSerializer):
    category = serializers.CharField(required=False)

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

    def validate_category(self, value):
        """
        Validate the category field to either retrieve or create the category
        based on the provided name.
        """
        if value:
            # Try to find the category by name, or create it if it doesn't exist
            category, created = Category.objects.get_or_create(name=value)
            return category  # Return the actual Category instance
        return None
