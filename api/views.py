from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from taggit.models import Tag

from .Pagination import CustomPageNumberPagination
from .filters import ProductFilter, InStockFilterBackend, ProductSearchFilterBackend
from .models import Product, Category, Order
from .serializers import ProductSerializer, CategorySerializer, OrderSerializer


class PaginationMixin:
    """
    Mixin to provide custom pagination for viewsets
    """
    pagination_class = CustomPageNumberPagination


class ProductViewSet(PaginationMixin, viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('category', 'tags')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
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
        Retrieve a personalized list of products.

        The response is personalized and incorporates the recommendation system.
        It is cached for 5 minutes, and the cache varies depending on the Authorization header.
        """
        qs = self.get_queryset()
        tag = None
        category = None
        tag_slug = self.request.query_params.get('tag', None)
        category_slug = self.request.query_params.get('category', None)

        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)  # Fetch the tag object or return 404
            qs = qs.filter(tags__in=[tag])  # Filter products by tag
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)  # Fetch the category object or return 404
            qs = qs.filter(category=category)  # Filter products by category


        self.queryset = qs  # Update the queryset with filtered results
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 60 * 24 * 7, key_prefix='product_list'))
    @method_decorator(vary_on_headers('Authorization'))
    @action(
        detail=False,
        methods=['get'],
        url_path='user-products',
        url_name='user_products'
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


class CategoryViewSet(PaginationMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer

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


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__product')
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        """
        Assign permissions based on the action being performed.
        """
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Disable order creation via the API.
        """
        return Response(
            {"detail": "Order creation is not allowed via this endpoint."},
            status=403
        )
