from django.urls import path
from .views import CartViewSet

urlpatterns = [
    path('cart/', CartViewSet.as_view({'get': 'list'}), name='cart-list'),
    path('cart/add/<uuid:product_id>/', CartViewSet.as_view({'post': 'add_to_cart'}), name='cart-add'),
    path('cart/remove/<uuid:product_id>/', CartViewSet.as_view({'delete': 'remove_from_cart'}), name='cart-remove'),
    path('cart/clear/', CartViewSet.as_view({'delete': 'clear_cart'}), name='cart-clear'),
]
