from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockAvailabilityView, SalesReportsView

router = DefaultRouter()
router.register(r'stock', StockAvailabilityView, basename='stock-availability')
router.register(r'reports', SalesReportsView, basename='sales-reports')

urlpatterns = [
    path('', include(router.urls)),
]