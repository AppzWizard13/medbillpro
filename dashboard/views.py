from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from accounts.permissions import IsAdminUser
from inventory.models import Medicine
from billing.models import Bill
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from inventory.serializers import MedicineSerializer

class StockAvailabilityView(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request):
        medicines = Medicine.objects.all()
        serializer = MedicineSerializer(medicines, many=True)
        return Response(serializer.data)

class SalesReportsView(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        staff_id = request.GET.get('staff_id')

        queryset = Bill.objects.all()

        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])

        if staff_id:
            queryset = queryset.filter(user_id=staff_id)

        sales_data = queryset.values('user').annotate(
            total_sales=Sum('total_price'),
            total_bills=Count('id')
        )

        return Response(sales_data)

class StaffPerformanceView(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        queryset = Bill.objects.all()

        if start_date and end_date:
            queryset = queryset.filter(created_at__range=[start_date, end_date])

        performance_data = queryset.values('user').annotate(
            total_sales=Sum('total_price'),
            total_bills=Count('id')
        )

        return Response(performance_data)