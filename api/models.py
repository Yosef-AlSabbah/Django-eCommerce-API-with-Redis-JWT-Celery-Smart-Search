from django.contrib.auth.models import AbstractUser
from django.db import models

from .utils import profile_upload_to_unique


class User(AbstractUser):
    email = models.EmailField(unique=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    picture = models.ImageField(upload_to=profile_upload_to_unique, null=True, blank=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        indexes = [
            models.Index(fields=['user']),
        ]
        ordering = ['user']

    def __str__(self):
        return f'{self.user.username} Profile'
