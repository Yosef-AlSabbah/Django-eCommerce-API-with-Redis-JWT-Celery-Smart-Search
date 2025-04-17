from django.urls import path

from .views import CartAPIView

urlpatterns = [
    path('', CartAPIView.as_view(), name='cart'),
    path('cart/<uuid:product_id>/', CartAPIView.as_view(), name='cart-product'),  # For POST and DELETE requests
]
