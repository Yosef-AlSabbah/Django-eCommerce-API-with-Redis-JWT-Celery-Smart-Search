
from django.core.cache import cache
from django.db.models import Q
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Category, Product, Review, Attribute, ProductAttribute
from .recommender import Recommender


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ['name', 'description']


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.ReadOnlyField()
    attributes = AttributeSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['name', 'slug', 'attributes']
        extra_kwargs = {'slug': {'read_only': True}}


class ProductAttributeSerializer(serializers.ModelSerializer):
    attribute = AttributeSerializer()

    class Meta:
        model = ProductAttribute
        fields = ['attribute', 'value']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
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
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    attributes_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    @extend_schema_field(serializers.DictField(child=serializers.FloatField()))
    def get_rating(self, obj):
        cache_key = f"product_{obj.product_id}_rating"
        cached_data = cache.get(cache_key)
        if cached_data is None:
            reviews = obj.reviews.all()
            if not reviews:
                return {"average": 0.0, "count": 0}
            total_rating = sum(review.rating for review in reviews)
            count = len(reviews)
            average_rating = total_rating / count
            cached_data = {"average": average_rating, "count": count, "total_rating": total_rating}
            cache.set(cache_key, cached_data, 604800)
        else:
            if cached_data["count"] > 0:
                cached_data["average"] = cached_data["total_rating"] / cached_data["count"]
            else:
                cached_data["average"] = 0.0
        return {"average": cached_data["average"], "count": cached_data["count"]}

    def to_internal_value(self, data):
        if self.instance is None and 'category' not in data:
            raise serializers.ValidationError(
                {'category': 'This field is required when creating a product.'}
            )
        return super().to_internal_value(data)

    def create(self, validated_data):
        tags = validated_data.pop('tags', None)
        attributes_data = validated_data.pop('attributes_data', [])
        instance = super().create(validated_data)
        if tags:
            instance.tags.set(tags['names'])

        for attr_data in attributes_data:
            attribute_name = attr_data.get('attribute_name')
            value = attr_data.get('value')
            if attribute_name and value is not None:
                attribute, _ = Attribute.objects.get_or_create(name=attribute_name)
                ProductAttribute.objects.create(product=instance, attribute=attribute, value=value)
        return instance

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        attributes_data = validated_data.pop('attributes_data', None)
        if tags:
            instance.tags.set(tags['names'])

        if attributes_data is not None:
            instance.attributes.all().delete()
            for attr_data in attributes_data:
                attribute_name = attr_data.get('attribute_name')
                value = attr_data.get('value')
                if attribute_name and value is not None:
                    attribute, _ = Attribute.objects.get_or_create(name=attribute_name)
                    ProductAttribute.objects.create(product=instance, attribute=attribute, value=value)

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
            'attributes',
            'attributes_data',
        ]


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created']
        read_only_fields = ['created']


class ProductDetailSerializer(ProductSerializer):
    recommended_products = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    def get_reviews(self, obj):
        reviews = obj.reviews.all()
        return ReviewSerializer(reviews, many=True, context=self.context).data

    def get_recommended_products(self, obj):
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
