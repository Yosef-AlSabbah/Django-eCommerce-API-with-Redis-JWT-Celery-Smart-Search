from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from account.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with default credentials (admin@admin.com / admin) and activated status and profile'

    def handle(self, *args, **options):
        email = 'admin@admin.com'
        username = 'admin'
        password = 'admin'
        first_name = 'Admin'
        last_name = 'User'

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'User with email "{email}" already exists.')
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'User with username "{username}" already exists.')
            )
            return

        try:
            # Create superuser
            user = User.objects.create_superuser(
                email=email,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=True  # Ensure user is activated
            )

            # Create profile for the user
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={'balance': 0.0}
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superuser "{username}" with email "{email}"'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(f'User is active: {user.is_active}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Profile created: {created}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )
