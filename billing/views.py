from rest_framework import viewsets, status
from rest_framework.response import Response
from .permissions import IsStaffUser
from .models import Bill
from .serializers import BillSerializer
from inventory.models import Medicine
from django.core.mail import send_mail

class BillingViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [IsStaffUser]

    def create(self, request, *args, **kwargs):
        try:
            medicine_id = request.data.get('medicine_id')
            quantity = int(request.data.get('quantity'))
            packaging_type = request.data.get('packaging_type')

            medicine = Medicine.objects.get(id=medicine_id)
            unit_price = getattr(medicine, f'price_{packaging_type}')
            total_price = unit_price * quantity

            # Prepare data for serializer
            bill_data = {
                'user': request.user.id,
                'medicine': medicine_id,
                'quantity': quantity,
                'packaging_type': packaging_type,
                'total_price': total_price,
                'unit_price': unit_price
            }

            serializer = self.get_serializer(data=bill_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            # Email
            invoice_details = f"Medicine: {medicine.name}, Quantity: {quantity}, Total Price: {total_price}"
            send_mail(
                'Your Invoice Details',
                invoice_details,
                'from@example.com',
                [request.user.email],
                fail_silently=False,
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Medicine.DoesNotExist:
            return Response({'error': 'Medicine not found'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
