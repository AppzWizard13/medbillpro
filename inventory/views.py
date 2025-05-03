from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Category, Medicine
from .serializers import MedicineSerializer
from .permissions import IsInventoryManager
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
User = get_user_model()

class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer

    def create(self, request, *args, **kwargs):
        def resolve_category(item):
            """Helper to resolve category by name, return error if not found."""
            category_name = item.get('category')
            try:
                category = Category.objects.get(name=category_name)
                item['category'] = category.name  
                return None
            except ObjectDoesNotExist:
                return f"Category '{category_name}' not found."

        if isinstance(request.data, list):
            valid_data = []
            errors = []

            for idx, item in enumerate(request.data):
                item_copy = item.copy()
                error = resolve_category(item_copy)
                if error:
                    errors.append({
                        'index': idx,
                        'name': item.get('name'),
                        'error': error
                    })
                    continue
                valid_data.append(item_copy)

            created_instances = []
            if valid_data:
                serializer = self.get_serializer(data=valid_data, many=True)
                serializer.is_valid(raise_exception=True)
                created_instances = serializer.save()

                for instance in created_instances:
                    instance.check_stock_and_expiry()

            return Response({
                'detail': 'Bulk creation processed.',
                'created_count': len(created_instances),
                'created': MedicineSerializer(created_instances, many=True).data,
                'failed': errors
            }, status=status.HTTP_207_MULTI_STATUS if errors else status.HTTP_201_CREATED)

        else:
            # Single object creation
            data = request.data.copy()
            error = resolve_category(data)
            if error:
                return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            instance.check_stock_and_expiry()
            return Response({
                'detail': 'Medicine created successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)




    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)  # Allow partial update (PATCH)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if not request.data:
            return Response({'detail': 'No fields provided for update.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.check_stock_and_expiry()
        return Response({
            'detail': 'Medicine updated successfully.',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'detail': 'Medicine deleted successfully.'}, status=status.HTTP_200_OK)
