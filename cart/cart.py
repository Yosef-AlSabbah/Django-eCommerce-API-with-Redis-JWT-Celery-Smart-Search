from decimal import Decimal

from django.conf import settings

from shop.models import Product


class Cart:
    def __init__(self, request):
        """
        Initialize the cart object by associating it with the current session.

        Args:
            request: The HTTP request object, which contains the session data.

        Attributes:
            session: The current session object.
            cart: A dictionary representing the cart stored in the session.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.

        Args:
            product: The product object to add or update in the cart.
            quantity: The number of units of the product to add (default is 1).
            override_quantity: If True, replace the current quantity with the given quantity.
                               If False, increment the current quantity by the given amount.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def remove(self, product):
        """
        Remove a product from the cart.

        Args:
            product: The product object to remove from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and retrieve the associated product objects
        from the database. Each item includes the product details, price, quantity,
        and total price.
        """
        product_ids = self.cart.keys()
        # get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Return the total number of items in the cart.

        Returns:
            int: The total quantity of all products in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate the total price of all items in the cart.

        Returns:
            Decimal: The total price of all items in the cart.
        """
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def save(self):
        """
        Mark the session as modified to ensure the cart data is saved.
        """
        self.session.modified = True

    def clear(self):
        """
        Clear all items from the cart by removing it from the session.
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()
