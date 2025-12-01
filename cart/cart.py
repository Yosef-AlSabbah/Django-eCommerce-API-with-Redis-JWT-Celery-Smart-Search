from decimal import Decimal

from django.conf import settings

from coupons.models import Coupon
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
        # store current applied coupon
        self.coupon_id = self.session.get('coupon_id')

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.

        Args:
            product: The product object to add or update in the cart.
            quantity: The number of units of the product to add (default is 1).
            override_quantity: If True, replace the current quantity with the given quantity.
                               If False, increment the current quantity by the given amount.
        """
        product_id = str(product.product_id)
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
        product_id = str(product.product_id)
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
        products = Product.objects.filter(product_id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.product_id)]['product'] = product
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
        del self.coupon_id
        self.save()

    @property
    def coupon(self):
        """
        Retrieve the currently applied coupon.

        Returns:
            Coupon: The applied coupon object if it exists and is valid.
            None: If no coupon is applied or the coupon does not exist.
        """
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)

            except Coupon.DoesNotExist:
                pass
        return None

    def get_discount(self, coupon=None):
        """
        Calculate the discount amount based on the provided coupon.
        If no coupon is provided, it uses the coupon from the session.

        Args:
            coupon (Coupon, optional): The coupon object to apply. Defaults to None.

        Returns:
            Decimal: The discount amount to be subtracted from the total price.
        """
        applied_coupon = coupon if coupon is not None else self.coupon
        if applied_coupon:
            return (
                applied_coupon.discount / Decimal(100)
            ) * self.get_total_price()
        return Decimal(0)

    def get_total_price_after_discount(self):
        """
        Calculate the total price of the cart after applying the discount.

        Returns:
            Decimal: The total price after the discount is applied.
        """
        return self.get_total_price() - self.get_discount()
