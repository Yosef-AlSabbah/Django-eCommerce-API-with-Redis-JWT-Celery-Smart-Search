
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from shop.models import Category, Product, Attribute
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
            'attributes_data': [
                {'attribute_name': 'Weight', 'value': 1.5},
                {'attribute_name': 'Color', 'value': 'Blue'},
                {'attribute_name': 'In Stock', 'value': True},
            ]
        }

    def test_valid_data(self):
        serializer = ProductSerializer(data=self.valid_data, context={'request': type('Request', (), {'user': self.user})})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_product_with_various_attribute_types(self):
        serializer = ProductSerializer(data=self.valid_data, context={'request': type('Request', (), {'user': self.user})})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        product = serializer.save(user=self.user)
        self.assertEqual(product.attributes.count(), 3)
        self.assertEqual(product.attributes.get(attribute__name='Weight').value, 1.5)
        self.assertEqual(product.attributes.get(attribute__name='Color').value, 'Blue')
        self.assertEqual(product.attributes.get(attribute__name='In Stock').value, True)

    def test_update_product_with_various_attribute_types(self):
        product = Product.objects.create(name='Old Product', description='desc', price=10, stock=10, category=self.category, user=self.user)
        update_data = {
            'attributes_data': [
                {'attribute_name': 'Price', 'value': 99.99},
                {'attribute_name': 'Available', 'value': False},
            ]
        }
        serializer = ProductSerializer(instance=product, data=update_data, partial=True, context={'request': type('Request', (), {'user': self.user})})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_product = serializer.save()
        self.assertEqual(updated_product.attributes.count(), 2)
        self.assertEqual(updated_product.attributes.get(attribute__name='Price').value, 99.99)
        self.assertEqual(updated_product.attributes.get(attribute__name='Available').value, False)

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
