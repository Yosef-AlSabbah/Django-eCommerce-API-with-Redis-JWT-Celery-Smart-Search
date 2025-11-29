from django.conf import settings
from django.db.models import Q

if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    from django.contrib.postgres.search import TrigramSimilarity

from ecommerce_api.utils.file_handling import upload_to_unique


def product_upload_to_unique(instance, filename):
    """
    Generate a unique file name for the product image.
    :param instance:
    :param filename:
    :return:
    """
    return upload_to_unique(instance, filename, directory="products/")


def search_products(queryset, search_term):
    """
    Centralized search function to filter products by name and description similarity.
    """
    if search_term:
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
            return queryset.annotate(
                name_similarity=TrigramSimilarity('name', search_term),
                description_similarity=TrigramSimilarity('description', search_term),
            ).filter(
                name_similarity__gt=0.1
            ).order_by('-name_similarity')
        else:
            return queryset.filter(
                Q(name__icontains=search_term) | Q(description__icontains=search_term)
            )
    return queryset
