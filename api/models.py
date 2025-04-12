import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify
from taggit.managers import TaggableManager

from .utils import product_upload_to_unique, profile_upload_to_unique


class User(AbstractUser):
    email = models.EmailField(unique=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    picture = models.ImageField(upload_to=profile_upload_to_unique, null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.name


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

    objects = models.Manager()
    tags = TaggableManager

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
