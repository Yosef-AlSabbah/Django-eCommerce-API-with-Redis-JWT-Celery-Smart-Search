from django.db import models
from django.utils import timezone
import datetime


class OTPCode(models.Model):
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_expired(self):
        return self.expires_at < timezone.now()

    def __str__(self):
        return f'{self.phone} - {self.code}'
