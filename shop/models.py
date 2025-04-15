import uuid

from django.db import models
from django.utils.text import slugify
from taggit.managers import TaggableManager

from .utils import product_upload_to_unique


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['name']),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"Category: {self.name}"


class Product(models.Model):
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
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

    def save(self, *args, **kwargs):
        # Auto-generate slug if not set or name changes
        if not self.slug or self.name != self.__class__.objects.get(pk=self.pk).name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Product: {self.name} (ID: {self.product_id})"
