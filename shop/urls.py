from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import ProductViewSet, CategoryViewSet, ReviewViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')

# Create a nested router for products/reviews
products_router = routers.NestedDefaultRouter(router, r'products', lookup='product')
products_router.register(r'reviews', ReviewViewSet, basename='product-reviews')

urlpatterns = []
urlpatterns += router.urls
urlpatterns += products_router.urls