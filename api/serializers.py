from rest_framework import serializers

from .models import Category, Product, User, Profile


class UserSerializer(serializers.ModelSerializer):
    class ProfileSerializer(serializers.ModelSerializer):
        class Meta:
            model = Profile
            fields = ['bio', 'location', 'birth_date', 'picture']

    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'profile', 'first_name', 'last_name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug']
        extra_kwargs = {'slug': {'read_only': True}}  # Make the slug field read-only


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()

    tags = serializers.ListField(
        child=serializers.CharField(),
        source='tags.names',
        required=False,
    )

    def to_internal_value(self, data):
        if self.instance is None and 'category' not in data:
            raise serializers.ValidationError(
                {'category': 'This field is required when creating a product.'}
            )
        return super().to_internal_value(data)

    def create(self, validated_data):
        # Custom create method to handle tags
        instance = super().create(**validated_data)  # Create the Product instance
        tags = validated_data.pop('tags', None)  # Extract tags from validated data
        if tags:
            instance.tags.set(*tags)  # Assign tags to the product
        return instance

    def update(self, instance, validated_data):
        # Custom update method to handle tags
        tags = validated_data.pop('tags', None)  # Extract tags from validated data
        if tags:
            instance.tags.clear()  # Clear existing tags
            instance.tags.set(*tags)  # Assign new tags
        else:
            instance.tags.clear()  # Clear tags if none are provided

        return super().update(instance, validated_data)

    class Meta:
        model = Product
        fields = [
            'product_id',
            'name',
            'slug',
            'description',
            'price',
            'stock',
            'image',
            'category',
            'tags'
        ]
