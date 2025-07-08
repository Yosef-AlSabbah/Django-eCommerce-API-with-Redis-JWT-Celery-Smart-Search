from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Category
from .models import Review


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, created=False, **kwargs):
    """
    Invalidate the cache for the category list when a category is created, updated or deleted.
    """
    import logging
    logger = logging.getLogger(__name__)

    action = "created" if kwargs.get('created', False) else "updated" if sender == post_save else "deleted"
    logger.info(f"Category {instance.name} was {action}, invalidating cache...")

    # Clear the custom category cache key
    try:
        # Clear the specific cache key used in the views
        cache.delete('category_list_custom')
        logger.info("Category cache invalidated successfully")

        # Also clear any cache_page patterns if they exist from other views
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern('*category_list*')
            cache.delete_pattern('*views.decorators.cache.cache_page*category_list*')
            logger.info("Cache patterns also cleared")

    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        try:
            # Fallback: Clear the entire cache if specific key deletion fails
            cache.clear()
            logger.info("Fallback: Entire cache cleared")
        except Exception as fallback_e:
            logger.error(f"Fallback cache clear also failed: {fallback_e}")

@receiver(post_save, sender=Review)
def update_rating_on_review_save(sender, instance, created, **kwargs):
    """
    Update the cached rating when a new review is created or an existing review is updated.

    Args:
        sender: The model class (Review).
        instance: The instance of the review being saved.
        created: Boolean indicating if the review was created (True) or updated (False).
    """
    product = instance.product
    cache_key = f"product_{product.product_id}_rating"
    cached_data = cache.get(cache_key)

    if cached_data is None:
        # If cache is not initialized, initialize it
        reviews = product.reviews.all()
        total_rating = sum(review.rating for review in reviews)
        count = len(reviews)
        average_rating = total_rating / count if count > 0 else 0.0
        cached_data = {"average": average_rating, "count": count, "total_rating": total_rating}
    else:
        # Incrementally update the cache
        if created:
            cached_data["total_rating"] += instance.rating
            cached_data["count"] += 1
        else:
            # For updates, adjust the total rating
            old_rating = instance.__class__.objects.get(pk=instance.pk).rating
            cached_data["total_rating"] += instance.rating - old_rating

        cached_data["average"] = cached_data["total_rating"] / cached_data["count"]

    cache.set(cache_key, cached_data, 604800)  # Cache for 1 week (604800 seconds)


@receiver(post_delete, sender=Review)
def update_rating_on_review_delete(sender, instance, **kwargs):
    """
    Update the cached rating when a review is deleted.

    Args:
        sender: The model class (Review).
        instance: The instance of the review being deleted.
    """
    product = instance.product
    cache_key = f"product_{product.product_id}_rating"
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        # Decrementally update the cache
        cached_data["total_rating"] -= instance.rating
        cached_data["count"] -= 1
        cached_data["average"] = (
            cached_data["total_rating"] / cached_data["count"] if cached_data["count"] > 0 else 0.0
        )
        cache.set(cache_key, cached_data, 604800)  # Cache for 1 week (604800 seconds)
