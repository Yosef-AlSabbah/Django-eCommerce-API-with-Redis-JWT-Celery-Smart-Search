from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from shop.models import Category
from shop.serializers import ProductSerializer

User = get_user_model()


class ProductSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.valid_data = {
            'name': 'New Product',
            'description': 'A valid description',
            'price': '25.50',
            'stock': 100,
            'category': self.category.slug,
            'weight': 1.5,
            'length': 10,
            'width': 10,
            'height': 10,
        }

    def test_valid_data(self):
        serializer = ProductSerializer(data=self.valid_data, context={'request': type('Request', (), {'user': self.user})})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_name_is_required(self):
        data = self.valid_data.copy()
        data.pop('name')
        serializer = ProductSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_price_must_be_positive(self):
        data = self.valid_data.copy()
        data['price'] = '-10.00'
        serializer = ProductSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)

    def test_stock_must_be_non_negative(self):
        data = self.valid_data.copy()
        data['stock'] = -1
        serializer = ProductSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('stock', serializer.errors)

    def test_category_must_exist(self):
        data = self.valid_data.copy()
        data['category'] = 'non-existent-category'
        serializer = ProductSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)

    def test_dimensions_must_be_positive(self):
        fields_to_test = ['weight', 'length', 'width', 'height']
        for field in fields_to_test:
            with self.subTest(field=field):
                data = self.valid_data.copy()
                data[field] = -5
                serializer = ProductSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)
