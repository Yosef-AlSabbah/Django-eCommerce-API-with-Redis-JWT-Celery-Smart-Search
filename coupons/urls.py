from rest_framework.routers import DefaultRouter

from coupons import views

router = DefaultRouter()
router.register('coupon', views.CouponViewSet, basename='coupon')

urlpatterns = []

urlpatterns += router.urls
