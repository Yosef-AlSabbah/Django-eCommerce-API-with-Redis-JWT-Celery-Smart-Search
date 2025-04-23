from rest_framework.routers import DefaultRouter

from .views import OrderViewSet

router = DefaultRouter()

router.register('orders', OrderViewSet)

urlpatterns = []

urlpatterns += router.urls
