from rest_framework import serializers

from .models import User, Profile


class UserSerializer(serializers.ModelSerializer):
    class ProfileSerializer(serializers.ModelSerializer):
        class Meta:
            model = Profile
            fields = ['bio', 'location', 'birth_date', 'picture']

    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'profile', 'first_name', 'last_name']
