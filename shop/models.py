import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from taggit.managers import TaggableManager

from .utils import product_upload_to_unique


class SluggedModel(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Auto-generate slug if not set or if name has changed.
        Includes the current date to ensure uniqueness.
        """
        from datetime import date

        if not self.slug:
            self.slug = f"{slugify(self.name)}-{date.today().strftime('%Y-%m-%d')}"
        else:
            try:
                existing = self.__class__.objects.get(pk=self.pk)
            except self.__class__.DoesNotExist:
                existing = None
            if existing and self.name != existing.name:
                self.slug = f"{slugify(self.name)}-{date.today().strftime('%Y-%m-%d')}"
        super().save(*args, **kwargs)


class Category(SluggedModel):
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
        ]
        ordering = ["name"]

    def get_absolute_url(self):
        return reverse('api-v1:category-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return f"Category: {self.name}"


class InStockManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(stock__gt=0)


class Product(SluggedModel):
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=product_upload_to_unique
    )
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="products",
        on_delete=models.CASCADE,
    )
    objects = models.Manager()
    in_stock = InStockManager()
    tags = TaggableManager()

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
        ordering = ["name"]

    def get_absolute_url(self):
        return reverse('api-v1:product-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return f"Product: {self.name} (ID: {self.product_id})"


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="reviews",
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reviews",
        on_delete=models.CASCADE
    )
    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )
    comment = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-created"]

    def __str__(self):
        return f"Review by {self.user} for {self.product} - {self.rating} stars"
