from django.urls import path

from .views import CalculateShippingCostAPIView, CityListAPIView

app_name = 'shipping'

urlpatterns = [
    path('calculate-cost/', CalculateShippingCostAPIView.as_view(), name='calculate-cost'),
    path('cities/', CityListAPIView.as_view(), name='city-list'),
]
