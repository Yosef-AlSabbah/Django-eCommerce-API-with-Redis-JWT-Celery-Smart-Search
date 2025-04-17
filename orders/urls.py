from rest_framework.routers import DefaultRouter

from orders.views import OrderViewSet

router = DefaultRouter()

router.register('orders', OrderViewSet)

urlpatterns = []

urlpatterns += router.urls
