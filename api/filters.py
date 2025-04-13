from django.contrib.postgres.search import TrigramSimilarity
from django_filters import FilterSet
from rest_framework.filters import BaseFilterBackend

from api.models import Product


class ProductFilter(FilterSet):
    """
    FilterSet for Product model.
    This filter allows filtering products based on various fields such as
    name, description, price, stock, category, and tags.
    """

    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'description': ['icontains'],
            'price': ['exact', 'lt', 'gt', 'range'],
            'stock': ['exact', 'lt', 'gt'],
            'category__name': ['exact', 'icontains'],
            'tags__name': ['exact', 'icontains'],
        }


class InStockFilterBackend(BaseFilterBackend):
    """
    Custom filter to only show products that are in stock.
    """

    def filter_queryset(self, request, queryset, view):
        return queryset.filter(stock__gt=0)


class ProductSearchFilterBackend(BaseFilterBackend):
    """
    Custom filter to search products by name and description.
    """

    def filter_queryset(self, request, queryset, view):
        search = request.query_params.get('search', None)
        if search:
            queryset.annotate(
                similarity=TrigramSimilarity('name', search),
            ).filter(similarity__gt=0.1).order_by('-similarity')
        return queryset
