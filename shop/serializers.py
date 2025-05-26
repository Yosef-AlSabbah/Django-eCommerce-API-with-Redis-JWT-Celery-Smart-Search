from django.core.cache import cache
from django.db.models import Q
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Category, Product, Review
from .recommender import Recommender


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField()

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

    slug = serializers.ReadOnlyField()
    thumbnail = serializers.ImageField(
        allow_null=True,
        required=False,
        use_url=True,
        max_length=255,
        help_text="URL of the product thumbnail image."
    )
    detail_url = serializers.URLField(source='get_absolute_url', read_only=True)

    @extend_schema_field(serializers.DictField(child=serializers.FloatField()))
    def get_rating(self, obj):
        """
        Calculate the average rating and count the number of users who rated the product.
        Cache the result for 1 week. The cache is updated incrementally when a review is created or deleted.

        Args:
            obj: The product instance.

        Returns:
            dict: A dictionary containing the average rating and the count of reviews.
        """
        cache_key = f"product_{obj.product_id}_rating"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            # Initialize cache if not present
            reviews = obj.reviews.all()
            if not reviews:
                return {"average": 0.0, "count": 0}  # No reviews, return 0.0 rating and count 0
            total_rating = sum(review.rating for review in reviews)
            count = len(reviews)
            average_rating = total_rating / count
            cached_data = {"average": average_rating, "count": count, "total_rating": total_rating}
            cache.set(cache_key, cached_data, 604800)  # Cache for 1 week (604800 seconds)
        else:
            # Update cache incrementally
            cached_data["average"] = cached_data["total_rating"] / cached_data["count"]

        return {"average": cached_data["average"], "count": cached_data["count"]}

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
            instance.tags.set(tags['names'])
        return instance

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags:
            instance.tags.set(tags['names'])
        # else:
        #     instance.tags.clear()
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
            'thumbnail',
            'detail_url',
            'category',
            'category_detail',
            'tags',
            'rating',
        ]


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Review
        fields = ['user', 'rating', 'comment', 'created']
        read_only_fields = ['created']


class ProductDetailSerializer(ProductSerializer):
    recommended_products = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    def get_reviews(self, obj):
        """
        Fetch reviews for the given product.
        """
        reviews = obj.reviews.all()
        return ReviewSerializer(reviews, many=True, context=self.context).data

    def get_recommended_products(self, obj):
        """
        Fetch recommended products for the given product.
        """
        recommender = Recommender()
        recommended_products = [product.product_id for product in
                                recommender.suggest_products_for([obj], max_results=5)]
        suggested_products = (
            Product.objects.filter(
                Q(category=obj.category) |
                Q(tags__in=obj.tags.all()) |
                Q(product_id__in=recommended_products)
            ).exclude(product_id=obj.product_id).distinct()[:10]
        )
        return ProductSerializer(suggested_products, many=True, context=self.context).data

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['recommended_products', 'reviews']
