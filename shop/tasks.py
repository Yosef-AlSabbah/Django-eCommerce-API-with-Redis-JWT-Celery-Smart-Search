from celery import shared_task
from django.core.cache import cache
from .recommender import Recommender
from .models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def update_user_recommendations(user_id):
    """
    Calculates and caches personalized recommendations for a given user.
    """
    try:
        user = User.objects.get(id=user_id)
        recommender = Recommender()

        # Get recommendation base from cart and order history
        recommendation_base = []

        # NOTE: We can't access the request/session in a Celery task,
        # so we can't get cart items. We'll rely on order history for now.

        recent_order_products = Product.objects.filter(order_items__order__user=user).distinct()[:20]
        recommendation_base.extend(recent_order_products)

        recommended_products = []
        if recommendation_base:
            recommended_products = recommender.suggest_products_for(recommendation_base, max_results=60)

        if len(recommended_products) < 20:
            fallback_random_products = list(Product.objects.all().order_by('?')[:40])
            recommended_products.extend(fallback_random_products)

        recommended_ids = [product.product_id for product in recommended_products]
        cache.set(f'user_recommendations:{user_id}', recommended_ids, timeout=3600 * 24) # Cache for 24 hours
    except User.DoesNotExist:
        # Handle case where user is not found
        pass
