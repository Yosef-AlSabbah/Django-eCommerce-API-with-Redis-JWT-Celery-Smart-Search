from django.urls import path, include

app_name = 'api-v1'

urlpatterns = [
    path('', include('shop.urls')),
    path('', include('orders.urls')),
    path('', include('cart.urls')),
    path('', include('coupons.urls')),
    path('', include('chat.urls')),
]
