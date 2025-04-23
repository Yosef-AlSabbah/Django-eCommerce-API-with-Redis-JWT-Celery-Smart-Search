from logging import getLogger

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)
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

logger = getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        operation_id=r"product\_list",
        description=r"List all products with filtering, ordering, and search capabilities. Cached for 5 minutes.",
        tags=[r"Products"],
        parameters=[
            OpenApiParameter(
                name=r"tag",
                description=r"Filter products by tag slug",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name=r"category",
                description=r"Filter products by category slug",
                required=False,
                type=str
            ),
        ],
        examples=[
            OpenApiExample(
                r"Example response",
                value={
                    "count": 100,
                    "next": r"http://api.example.com/products/?page=2",
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "name": "Sample Product",
                            "price": "19.99",
                            "stock": 50,
                            "slug": "sample-product"
                        }
                    ]
                }
            )
        ]
    ),
    retrieve=extend_schema(
        operation_id=r"product\_retrieve",
        description=r"Retrieve a single product by slug. Cached for 1 hour.",
        tags=[r"Products"],
        responses={
            200: OpenApiResponse(description=r"Product details retrieved successfully."),
            404: OpenApiResponse(description=r"Product not found."),
        }
    ),
    create=extend_schema(
        operation_id=r"product\_create",
        description=r"Create a new product. Requires authentication and ownership/staff status.",
        tags=[r"Products"],
        responses={
            201: OpenApiResponse(description=r"Product created successfully."),
            400: OpenApiResponse(description=r"Invalid input data."),
            401: OpenApiResponse(description=r"Authentication required."),
            403: OpenApiResponse(description=r"Permission denied - must be owner or staff."),
        }
    ),
    update=extend_schema(
        operation_id=r"product\_update",
        description=r"Update an existing product. Requires ownership or staff status.",
        tags=[r"Products"],
        responses={
            200: OpenApiResponse(description=r"Product updated successfully."),
            400: OpenApiResponse(description=r"Invalid input data."),
            401: OpenApiResponse(description=r"Authentication required."),
            403: OpenApiResponse(description=r"Permission denied - must be owner or staff."),
            404: OpenApiResponse(description=r"Product not found."),
        }
    ),
    partial_update=extend_schema(
        operation_id=r"product\_partial\_update",
        description=r"Partially update an existing product. Requires ownership or staff status.",
        tags=[r"Products"],
        responses={
            200: OpenApiResponse(description=r"Product updated successfully."),
            400: OpenApiResponse(description=r"Invalid input data."),
            401: OpenApiResponse(description=r"Authentication required."),
            403: OpenApiResponse(description=r"Permission denied - must be owner or staff."),
            404: OpenApiResponse(description=r"Product not found."),
        }
    ),
    destroy=extend_schema(
        operation_id=r"product\_destroy",
        description=r"Delete a product. Requires ownership or staff status.",
        tags=[r"Products"],
        responses={
            204: OpenApiResponse(description=r"Product deleted successfully."),
            401: OpenApiResponse(description=r"Authentication required."),
            403: OpenApiResponse(description=r"Permission denied - must be owner or staff."),
            404: OpenApiResponse(description=r"Product not found."),
        }
    ),
    list_user_products=extend_schema(
        operation_id=r"product\_list\_user",
        description=r"List products belonging to the authenticated user. Cached for 1 week.",
        tags=[r"Products"],
        responses={
            200: OpenApiResponse(description=r"User products retrieved successfully."),
            401: OpenApiResponse(description=r"Authentication required."),
        }
    ),
)
class ProductViewSet(PaginationMixin, viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related(r'category', r'tags')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrStaff]
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        InStockFilterBackend,
        ProductSearchFilterBackend,
    ]
    ordering_fields = [r'name', r'price', r'stock']
    lookup_field = r'slug'

    @method_decorator(cache_page(60 * 5, key_prefix=r'product_list'))
    @method_decorator(vary_on_headers(r'Authorization'))
    def list(self, request, *args, **kwargs):
        try:
            logger.info("Listing products for user id: %s", request.user.id)
            queryset = self.get_queryset()
            tag_slug = request.query_params.get(r'tag')
            category_slug = request.query_params.get(r'category')
            if tag_slug:
                tag = get_object_or_404(Tag, slug=tag_slug)
                queryset = queryset.filter(tags__in=[tag])
            if category_slug:
                category = get_object_or_404(Category, slug=category_slug)
                queryset = queryset.filter(category=category)
            recommender = Recommender()
            cart = Cart(request)
            recommendation_base = [item[r'product'] for item in cart]
            if request.user.is_authenticated:
                recent_order_products = Product.objects.filter(order_items__order__user=request.user).distinct()[:20]
                recommendation_base.extend(recent_order_products)
            recommended_products = []
            if recommendation_base:
                recommended_products = recommender.suggest_products_for(recommendation_base, max_results=60)
            if len(recommended_products) < 20:
                fallback_random_products = list(Product.objects.all().order_by(r'?')[:40])
                recommended_products.extend(fallback_random_products)
            recommended_ids = [product.product_id for product in recommended_products]
            self.queryset = queryset.filter(product_id__in=recommended_ids)
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error("Error listing products: %s", e, exc_info=True)
            raise

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
            logger.info("Product created by user id: %s", self.request.user.id)
        except Exception as e:
            logger.error("Error creating product for user id: %s: %s", self.request.user.id, e, exc_info=True)
            raise

    @method_decorator(cache_page(60 * 60, key_prefix=r'user_product_detail'))
    def retrieve(self, request, *args, **kwargs):
        try:
            logger.info("Retrieving product detail for slug: %s", kwargs.get(r'slug'))
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            logger.error("Error retrieving product: %s", e, exc_info=True)
            raise

    @action(detail=False, methods=[r'get'], url_path=r'user-products', url_name=r'user-products')
    def list_user_products(self, request):
        try:
            logger.info("Listing products for user id: %s", request.user.id)
            user = request.user
            queryset = self.queryset.filter(user=user)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error("Error listing user products: %s", e, exc_info=True)
            raise

    def get_permissions(self):
        if self.action in [r'list_user_products']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()


@extend_schema_view(
    list=extend_schema(
        operation_id=r"category\_list",
        description=r"List all product categories. Publicly accessible. Cached for 24 hours.",
        tags=[r"Categories"],
        responses={
            200: OpenApiResponse(description=r"Categories retrieved successfully."),
        }
    ),
    retrieve=extend_schema(
        operation_id=r"category\_retrieve",
        description=r"Retrieve a single category by slug.",
        tags=[r"Categories"],
        responses={
            200: OpenApiResponse(description=r"Category details retrieved successfully."),
            404: OpenApiResponse(description=r"Category not found."),
        }
    ),
    create=extend_schema(
        operation_id=r"category\_create",
        description=r"Create a new category. Requires admin privileges.",
        tags=[r"Categories"],
        responses={
            201: OpenApiResponse(description=r"Category created successfully."),
            400: OpenApiResponse(description=r"Invalid input data."),
            401: OpenApiResponse(description=r"Authentication required."),
            403: OpenApiResponse(description=r"Admin privileges required."),
        }
    ),
    update=extend_schema(
        operation_id=r"category\_update",
        description=r"Update an existing category. Requires admin privileges.",
        tags=[r"Categories"],
        responses={
            200: OpenApiResponse(description=r"Category updated successfully."),
            400: OpenApiResponse(description=r"Invalid input data."),
            401: OpenApiResponse(description=r"Authentication required."),
            403: OpenApiResponse(description=r"Admin privileges required."),
            404: OpenApiResponse(description=r"Category not found."),
        }
    ),
    partial_update=extend_schema(
        operation_id=r"category\_partial\_update",
        description=r"Partially update an existing category. Requires admin privileges.",
        tags=[r"Categories"],
        responses={
            200: OpenApiResponse(description=r"Category updated successfully."),
            400: OpenApiResponse(description=r"Invalid input data."),
            401: OpenApiResponse(description=r"Authentication required."),
            403: OpenApiResponse(description=r"Admin privileges required."),
            404: OpenApiResponse(description=r"Category not found."),
        }
    ),
    destroy=extend_schema(
        operation_id=r"category\_destroy",
        description=r"Delete a category. Requires admin privileges.",
        tags=[r"Categories"],
        responses={
            204: OpenApiResponse(description=r"Category deleted successfully."),
            401: OpenApiResponse(description=r"Authentication required."),
            403: OpenApiResponse(description=r"Admin privileges required."),
            404: OpenApiResponse(description=r"Category not found."),
        }
    ),
)
class CategoryViewSet(PaginationMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    lookup_field = r'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

    @method_decorator(cache_page(60 * 60 * 24, key_prefix=r'category_list'))
    def list(self, request, *args, **kwargs):
        try:
            logger.info("Listing categories")
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error("Error listing categories: %s", e, exc_info=True)
            raise
