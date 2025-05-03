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
from django.db.models import Sum, Count, F
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.db.models import Sum, Count, F

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
        username = request.GET.get('username')
        group_by = request.GET.get('group_by', 'staff')

        queryset = Bill.objects.select_related('staff_user').all()

        # Date range filtering
        if start_date and end_date:
            queryset = queryset.filter(created_at__date__range=[start_date, end_date])

        # Staff filtering by username
        staff_user = None
        if username:
            try:
                staff_user = User.objects.get(username=username)
                queryset = queryset.filter(staff_user=staff_user)
            except User.DoesNotExist:
                return Response(
                    {"error": f"Staff with username '{username}' not found."},
                    status=404
                )

        # Grouping logic
        if group_by == 'staff':
            sales_data = queryset.values(
                'staff_user__id',
                'staff_user__username',
                'staff_user__first_name',
                'staff_user__last_name'
            ).annotate(
                total_sales=Sum('total_amount'),
                total_bills=Count('id'),
                average_bill=F('total_sales') / F('total_bills')
            ).order_by('-total_sales')

        elif group_by == 'day':
            sales_data = queryset.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                total_sales=Sum('total_amount'),
                total_bills=Count('id'),
                average_bill=F('total_sales') / F('total_bills')
            ).order_by('date')

        elif group_by == 'week':
            sales_data = queryset.annotate(
                week=TruncWeek('created_at')
            ).values('week').annotate(
                total_sales=Sum('total_amount'),
                total_bills=Count('id'),
                average_bill=F('total_sales') / F('total_bills')
            ).order_by('week')

        elif group_by == 'month':
            sales_data = queryset.annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                total_sales=Sum('total_amount'),
                total_bills=Count('id'),
                average_bill=F('total_sales') / F('total_bills')
            ).order_by('month')

        else:
            return Response(
                {"error": "Invalid group_by parameter. Valid options are: staff, day, week, month"},
                status=400
            )

        # Return staff details if filtered by username
        if username and staff_user:
            staff_data = {
                "id": staff_user.id,
                "username": staff_user.username,
                "first_name": staff_user.first_name,
                "last_name": staff_user.last_name,
                "email": staff_user.email,
            }
            return Response({
                "staff": staff_data,
                "sales_data": sales_data
            })

        return Response(sales_data)