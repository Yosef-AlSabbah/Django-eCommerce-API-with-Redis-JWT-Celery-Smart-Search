import unittest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from shop.models import Category, Product


class FilterTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(email='testuser@example.com', password='testpassword')
        cls.category1 = Category.objects.create(name='Electronics')
        cls.category2 = Category.objects.create(name='Books')

        cls.product1 = Product.objects.create(
            name='Laptop', description='A powerful laptop for programming', price=1200.00, stock=10,
            category=cls.category1, user=cls.user, weight=2.5, length=40, width=30, height=5,
        )
        cls.product1.tags.add('tech', 'computers')

        cls.product2 = Product.objects.create(
            name='Smartphone', description='A modern smartphone with a great camera', price=800.00, stock=5,
            category=cls.category1, user=cls.user, weight=0.5, length=15, width=7, height=1,
        )
        cls.product2.tags.add('tech', 'mobile')

        cls.product3 = Product.objects.create(
            name='Python Crash Course', description='A book about Python programming', price=30.00, stock=0,
            category=cls.category2, user=cls.user, weight=1, length=25, width=20, height=3,
        )
        cls.product3.tags.add('programming', 'python', 'books')

        cls.product4 = Product.objects.create(
            name='The Pragmatic Programmer', description='Another book about software development', price=45.00, stock=20,
            category=cls.category2, user=cls.user, weight=1.2, length=25, width=20, height=4,
        )
        cls.product4.tags.add('programming', 'software', 'books')

        cls.client = APIClient()
        cls.url = reverse('api-v1:product-list')

    def test_filter_by_name_exact(self):
        response = self.client.get(self.url, {'name': 'Laptop'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'Laptop')

    def test_filter_by_name_icontains(self):
        response = self.client.get(self.url, {'name__icontains': 'laptop'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'Laptop')

    def test_filter_by_price_exact(self):
        response = self.client.get(self.url, {'price': 800.00})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'Smartphone')

    def test_filter_by_price_range(self):
        response = self.client.get(self.url, {'price__range': '700,1300'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

    def test_filter_by_category_slug(self):
        response = self.client.get(self.url, {'category__slug': 'electronics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

    def test_filter_by_tags_name(self):
        response = self.client.get(self.url, {'tags__name': 'tech'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

    def test_filter_by_stock_gt(self):
        response = self.client.get(self.url, {'stock__gt': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

    def test_in_stock_filter_backend(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 3 products are in stock
        self.assertEqual(len(response.data['data']), 3)

    @unittest.skip("Search filter needs rework")
    def test_product_search_filter_backend(self):
        response = self.client.get(self.url, {'search': 'programming'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)
