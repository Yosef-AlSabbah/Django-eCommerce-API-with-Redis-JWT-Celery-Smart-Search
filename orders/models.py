import uuid

from django.db import models

from api.models import User
from shop.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PE', 'Pending'
        COMPLETED = 'CO', 'Completed'
        CANCELLED = 'CA', 'Cancelled'

    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    order_date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['-order_date']),
        ]
        ordering = ["-order_date"]

    @property
    def total_price(self):
        """
        Calculate the total price of the order.

        Returns:
            Decimal: The total price, which is the sum of all order items' prices.
        """
        return sum(item.price for item in self.items.all())

    def __str__(self):
        return f"Order: {self.id} by {self.user.username if self.user else 'Deleted User'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
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
