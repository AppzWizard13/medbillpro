from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Medicine
from .serializers import MedicineSerializer
from .permissions import IsInventoryManager


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsInventoryManager]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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
