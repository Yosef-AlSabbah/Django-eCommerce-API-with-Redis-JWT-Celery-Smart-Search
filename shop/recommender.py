import redis
from django.conf import settings

from .models import Product

# connect to redis
r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
)


class Recommender:
    def get_product_key(self, id):
        return f'product:{id}:purchased_with'

    def products_bought(self, products):
        product_ids = [p.id for p in products]
        for product_id in product_ids:
            for with_id in product_ids:
                # get the other products bought with each product
                if product_id != with_id:
                    # increment score for product purchased together
                    r.zincrby(
                        self.get_product_key(product_id), 1, with_id
                    )

    def suggest_products_for(self, products, max_results=6):
        product_ids = [str(p.product_id) for p in products]
        if len(products) == 1:
            # only 1 product
            suggestions = r.zrange(
                self.get_product_key(product_ids[0]), 0, -1, desc=True
            )[:max_results]
        else:
            # generate a temporary key
            flat_ids = ''.join([str(id) for id in product_ids])
            tmp_key = f'tmp_{flat_ids}'
            # multiple products, combine scores of all products
            # store the resulting sorted set in a temporary key
            keys = [self.get_product_key(id) for id in product_ids]
            r.zunionstore(tmp_key, keys)
            # remove ids for the products the recommendation is for
            r.zrem(tmp_key, *product_ids)
            # get the product ids by their score, descendant sort
            suggestions = r.zrange(
                tmp_key, 0, -1, desc=True
            )[:max_results]
            # remove the temporary key
            r.delete(tmp_key)
        suggested_products_ids = [str(id) for id in suggestions]
        # get suggested products and sort by order of appearance
        suggested_products = list(
            Product.objects.filter(product_id__in=suggested_products_ids)
        )
        suggested_products.sort(
            key=lambda x: suggested_products_ids.index(x.product_id)
        )
        return suggested_products
    #
    # def suggest_for_user(self, user, max_results=100):
    #     """
    #     Suggest products for the logged-in user based on their previous purchases.
    #     """
    #     # Get the products purchased by the user
    #     purchased_products = Product.objects.filter(
    #         order__user=user
    #     ).distinct()  # Assuming an `Order` model exists with a `user` field
    #
    #     if not purchased_products.exists():
    #         return []  # Return an empty list if no purchases are found
    #
    #     # Use the existing recommendation logic
    #     return self.suggest_products_for(purchased_products, max_results=max_results)
