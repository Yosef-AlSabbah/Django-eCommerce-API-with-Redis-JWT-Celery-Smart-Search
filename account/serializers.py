from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Profile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for handling the current user's profile, combining User and Profile fields."""
    # Serialize fields from the User model directly
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    password = serializers.CharField(write_only=True, required=True, source="user.password")
    phone_number = serializers.CharField(source="user.phone_number", required=False)

    # Fields from the Profile model
    profile_pic = serializers.ImageField(
        required=False,
        help_text="Upload a profile picture (max size 2MB).",
        use_url=True,
    )

    class Meta:
        model = Profile
        fields = [
            "username", "email", "password", "first_name", "last_name",
            "phone_number", "profile_pic",
        ]

    def validate_profile_pic(self, value):
        """Validate that the uploaded profile picture does not exceed 2MB."""
        if value and value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Profile picture size should not exceed 2MB.")
        return value

    def validate_phone_number(self, value):
        """
        Validate the phone number format.
        """
        if not value:
            return value  # Allow blank phone numbers if the field is optional

        import re
        pattern = r'^\+?1?\d{9,15}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        return value

    def create(self, validated_data):
        """Create a new user and their profile."""
        user_data = validated_data.pop("user")
        profile_pic = validated_data.pop("profile_pic", None)

        with transaction.atomic():
            # Create the User instance
            user = User.objects.create_user(**user_data)
            user.set_password(user_data["password"])
            user.save()

            # Create the Profile instance
            profile = Profile.objects.create(user=user, **validated_data)

            # Attach profile_pic if provided
            if profile_pic:
                profile.profile_pic = profile_pic
                profile.save()

        return profile

    def update(self, instance, validated_data):
        """Update the user's profile and associated user fields."""
        user_data = validated_data.pop("user", {})
        profile_pic = validated_data.pop("profile_pic", None)

        # Update User fields
        user = self.context["request"].user
        for attr, value in user_data.items():
            if attr == "password":
                user.set_password(value)
            else:
                setattr(user, attr, value)
        user.save()

        # Update Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if profile_pic:
            instance.profile_pic = profile_pic

        instance.save()
        return instance


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, help_text="Refresh token to be blacklisted")
