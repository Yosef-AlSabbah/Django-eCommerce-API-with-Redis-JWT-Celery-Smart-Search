from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create a Profile whenever a new User is created.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(user_logged_in)
def update_last_login_ip(sender, request, user, **kwargs):
    user.last_login_ip = request.META.get('REMOTE_ADDR')
    user.last_login = timezone.now()
    user.save()
