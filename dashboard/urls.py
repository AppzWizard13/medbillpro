from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockAvailabilityView, SalesReportsView, StaffPerformanceView

router = DefaultRouter()
router.register(r'stock', StockAvailabilityView, basename='stock-availability')
router.register(r'reports', SalesReportsView, basename='sales-reports')
router.register(r'performance', StaffPerformanceView, basename='staff-performance')

urlpatterns = [
    path('', include(router.urls)),
]