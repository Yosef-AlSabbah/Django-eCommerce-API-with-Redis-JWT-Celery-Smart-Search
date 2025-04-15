from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Category


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """
    Invalidate the cache for the category list when a category is created or deleted.
    """
    from django.core.cache import cache

    # Clear the cache for the category list
    cache.delete_pattern('*category_list*')
