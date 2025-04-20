from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from taggit.models import Tag

from cart.cart import Cart
from ecommerce_api.core.mixins import PaginationMixin
from ecommerce_api.core.permissions import IsOwnerOrStaff
from shop.filters import ProductFilter, InStockFilterBackend, ProductSearchFilterBackend
from .models import Product, Category
from .recommender import Recommender
from .serializers import ProductSerializer, CategorySerializer


class ProductViewSet(PaginationMixin, viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('category', 'tags')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrStaff]
    serializer_class = ProductSerializer
    filterset_class = ProductFilter  # Use custom filter class for filtering products
    filter_backends = [
        DjangoFilterBackend,  # Enable Django-style filtering
        OrderingFilter,  # Allow ordering of results
        InStockFilterBackend,  # Custom backend for filtering in-stock products
        ProductSearchFilterBackend,  # Custom backend for search functionality
    ]
    ordering_fields = ['name', 'price', 'stock']  # Fields allowed for ordering
    lookup_field = 'slug'  # Use slug instead of ID for lookups

    @method_decorator(cache_page(60 * 5, key_prefix='product_list'))
    @method_decorator(vary_on_headers('Authorization'))
    def list(self, request, *args, **kwargs):
        """
        Retrieve a personalized list of products with recommendations.

        This method filters products based on query parameters (tag and category),
        incorporates a recommendation system, and caches the response for 5 minutes.
        The cache varies depending on the Authorization header.

        Steps:
        1. Filter products by tag and category if provided.
        2. Gather products for recommendations:
           - Products in the user's cart.
           - Products from the user's recent orders (if authenticated).
        3. Generate recommendations using the `Recommender` class.
        4. Include fallback random products if recommendations are insufficient.
        5. Return the filtered and paginated product list.
        """
        # Filter products by tag and category
        queryset = self.get_queryset()
        tag_slug = request.query_params.get('tag')
        category_slug = request.query_params.get('category')

        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags__in=[tag])
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)

        # Initialize recommender and cart
        recommender = Recommender()
        cart = Cart(request)

        # Gather products for recommendations
        recommendation_base = [item['product'] for item in cart]
        if request.user.is_authenticated:
            recent_order_products = Product.objects.filter(
                order_items__order__user=request.user
            ).distinct()[:20]
            recommendation_base.extend(recent_order_products)

        # Initialize an empty list to store recommended products
        recommended_products = []

        # If there are products in the recommendation base, generate recommendations
        if recommendation_base:
            # Use the recommender to suggest up to 60 products based on the recommendation base
            recommended_products = recommender.suggest_products_for(recommendation_base, max_results=60)

        # If the number of recommended products is less than 20, add fallback random products
        if len(recommended_products) < 20:
            # Fetch up to 40 random products from the database as a fallback
            fallback_random_products = list(Product.objects.all().order_by('?')[:40])
            # Extend the recommended products list with the fallback products
            recommended_products.extend(fallback_random_products)

        # Filter queryset to include only recommended products
        recommended_product_ids = [product.product_id for product in recommended_products]
        queryset = queryset.filter(product_id__in=recommended_product_ids)

        # Update the queryset and return the response
        self.queryset = queryset
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 60 * 24 * 7, key_prefix='user_product_list'))
    @method_decorator(vary_on_headers('Authorization'))
    @action(
        detail=False,
        methods=['get'],
        url_path='user-products',
        url_name='user-products',

    )
    def list_user_products(self, request):
        """
        Retrieve a paginated list of products for the logged-in user.

        The response will be cached for 1 week but will be invalidated
        if the user updates their products in any way.
        """
        user = request.user
        queryset = self.queryset.filter(user=user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @method_decorator(cache_page(60 * 60, key_prefix='user_product_detail'))
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single product detail.

        This method retrieves the details of a specific product based on the `slug`
        provided in the URL. The response is cached for 1 hour to improve performance
        and reduce database queries.

        Caching Key: Varies based on the `user_product_detail` key prefix.
        """
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Automatically assign the logged-in user as the owner of the product.
        """
        serializer.save(user=self.request.user)

    def get_permissions(self):
        """
        Assign permissions based on the action being performed.
        """
        if self.action in ['list_user_products']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()


class CategoryViewSet(PaginationMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def get_permissions(self):
        """
        Assign permissions based on the action being performed.
        """
        if self.action == 'list':
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

    @method_decorator(cache_page(60 * 60 * 24, key_prefix='category_list'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
