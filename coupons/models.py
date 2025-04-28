from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.timezone import now


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Coupon Code")
    valid_from = models.DateTimeField(verbose_name="Valid From")
    valid_to = models.DateTimeField(verbose_name="Valid To")
    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage value (0 to 100)",
        verbose_name="Discount Percentage"
    )
    active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["valid_from", "valid_to"]),
        ]
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ["code"]

    def clean(self):
        if self.valid_from >= self.valid_to:
            raise ValidationError("`valid_from` must be earlier than `valid_to`.")

    def is_valid(self):
        return self.active and self.valid_from <= now() <= self.valid_to

    def __str__(self):
        return self.code
