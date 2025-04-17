from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from shop.models import Category

User = get_user_model()


class CategoryTests(APITestCase):
    """
    Test suite for the Category API endpoints.
    """

    def setUp(self):
        """
        Set up test data for the Category tests.
        """
        self.user = User.objects.create_user(username='user', password='pass')
        self.admin = User.objects.create_superuser(username='admin', password='pass', email='<EMAIL>')
        self.category = Category.objects.create(name='Computers', slug='computers')
        self.category = Category.objects.create(name='category2', slug='category2')
        self.category_data = {
            'name': 'Electronics',
            'slug': 'electronics'
        }
        self.url = reverse('api-v1:category-list')

    def test_list_categories(self):
        """
        Test the list categories endpoint.
        """
        url = self.url
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url)

        # test unauthenticated access
        self.assertEqual(response.status_code, 200)

        # test authenticated access
        self.client.login(username='user', password='pass')
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)

    def test_authenticated_list_categories(self):
        """
        Test the list categories endpoint.
        """
        url = self.url
        self.client.login(username='user', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Computers')

    def test_admin_can_create_category(self):
        self.client.login(username='admin', password='pass')
        response = self.client.post(self.url, {'name': 'Electronics', 'slug': 'electronics'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_admin_cannot_create_category(self):
        self.client.login(username='user', password='pass')
        response = self.client.post(self.url, {'name': 'Electronics', 'slug': 'electronics'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unique_slug_constraint(self):
        self.client.login(username='admin', password='pass')
        response = self.client.post(self.url, {'name': 'Duplicate', 'slug': 'computers'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('slug', response.data)


class ProductConstraintTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='pass', email='admin@example.com')
        self.category = Category.objects.create(name='Computers', slug='computers')
        self.url = reverse('api-v1:product-list')

    def test_create_product_with_missing_fields(self):
        self.client.login(username='admin', password='pass')
        response = self.client.post(self.url, {'name': 'Laptop'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('price', response.data)
        self.assertNotIn('category', response.data)

    def test_unique_slug_constraint(self):
        self.client.login(username='admin', password='pass')
        product_data = {
            'name': 'Laptop',
            'slug': 'laptop',
            'description': 'A powerful laptop',
            'price': 1000.00,
            'stock': 10,
            'category': self.category.id
        }
        self.client.post(self.url, product_data)
        response = self.client.post(self.url, product_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_product_requires_category_and_user(self):
        self.client.login(username='admin', password='pass')
        product_data = {
            'name': 'Laptop',
            'slug': 'laptop',
            'description': 'A powerful laptop',
            'price': 1000.00,
            'stock': 10,
        }
        response = self.client.post(self.url, product_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_product_list_shows_only_user_products(self):
        self.client.login(username='admin', password='pass')
        product_data = {
            'name': 'Laptop',
            'slug': 'laptop',
            'description': 'A powerful laptop',
            'price': 1000.00,
            'stock': 10,
            'category': self.category.id,
        }
        response = self.client.post(self.url, product_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('api-v1:product-user-products')
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
