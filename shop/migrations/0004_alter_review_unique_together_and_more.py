# Generated by Django 5.2 on 2025-04-29 11:58

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_rename_image_product_thumbnail'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='review',
            unique_together={('product', 'user')},
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['product'], name='shop_review_product_d2a5c4_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['user'], name='shop_review_user_id_fcb4ba_idx'),
        ),
    ]
