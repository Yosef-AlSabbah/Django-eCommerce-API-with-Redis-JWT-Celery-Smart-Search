from django.core.cache import cache
from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug']
        extra_kwargs = {'slug': {'read_only': True}}  # Make the slug field read-only


class ProductSerializer(serializers.ModelSerializer):
    # Use PrimaryKeyRelatedField for input and CategorySerializer for output
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True
    )
    category_detail = CategorySerializer(source='category', read_only=True)

    tags = serializers.ListField(
        child=serializers.CharField(),
        source='tags.names',
        required=False,
    )
    rating = serializers.SerializerMethodField()

    def get_rating(self, obj):
        """
        Calculate the average rating for the product and cache it for 1 hour.
        """
        cache_key = f"product_{obj.product_id}_rating"
        rating = cache.get(cache_key)

        if rating is None:
            reviews = obj.reviews.all()
            if not reviews:
                return None
            total_rating = sum(review.rating for review in reviews)
            rating = total_rating / len(reviews)
            cache.set(cache_key, rating, 3600)  # Cache for 1 hour (3600 seconds)

        return rating

    def to_internal_value(self, data):
        if self.instance is None and 'category' not in data:
            raise serializers.ValidationError(
                {'category': 'This field is required when creating a product.'}
            )
        return super().to_internal_value(data)

    def create(self, validated_data):
        tags = validated_data.pop('tags', None)
        instance = super().create(validated_data)
        if tags:
            instance.tags.set(*tags)
        return instance

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags:
            instance.tags.set(*tags)
        else:
            instance.tags.clear()
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
            'category_detail',
            'tags',
            'rating',
        ]
