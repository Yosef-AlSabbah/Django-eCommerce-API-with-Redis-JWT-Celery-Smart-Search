import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from coupons.models import Coupon
from shop.models import Product

User = get_user_model()


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PE', 'Pending'
        COMPLETED = 'CO', 'Completed'
        CANCELLED = 'CA', 'Cancelled'

    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='orders', on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    order_date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    coupon = models.ForeignKey(Coupon, related_name='orders', on_delete=models.SET_NULL, null=True)
    stripe_id = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['-order_date']),
        ]
        ordering = ["-order_date"]

    def get_total_cost_before_discount(self):
        """
        Calculate the total cost of all items in the order before applying any discounts.

        Returns:
            Decimal: The total cost of all order items.
        """
        return sum(item.price for item in self.items.all())

    def get_discount(self):
        """
        Calculate the discount amount for the order based on the associated coupon.

        Returns:
            Decimal: The discount amount. Returns 0 if no coupon is applied.
        """
        total_cost = self.get_total_cost_before_discount()

        if self.coupon:
            return total_cost * (self.coupon.discount / Decimal(100))
        return Decimal(0)

    @property
    def total_price(self):
        """
        Calculate the total price of the order after applying any discounts.

        Returns:
            Decimal: The total price, which is the total cost of all order items minus the discount.
        """
        total_cost = self.get_total_cost_before_discount()
        return total_cost - self.get_discount()

    def get_stripe_url(self):
        if not self.stripe_id:
            # no payment associated
            return ''
        if '_test_' in settings.STRIPE_SECRET_KEY:
            # Stripe path for test payments
            path = '/test/'
        else:
            # Stripe path for real payments
            path = '/'
            return f'https://dashboard.stripe.com{path}payments/{self.stripe_id}'

    def __str__(self):
        return f"Order: {self.id} by {self.user.username if self.user else 'Deleted User'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]
        ordering = ["order"]

    @property
    def price(self):
        """
        Calculate the total price for the order item.

        Returns:
            Decimal: The total price, which is the product of the item's price and quantity.
        """
        return self.product.price * self.quantity

    def __str__(self):
        return f"Order Item: {self.product.name} (Order ID: {self.order.id})"
