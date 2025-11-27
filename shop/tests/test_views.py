from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from shop.models import Category, Product, Review
from orders.models import Order, OrderItem

User = get_user_model()


class CategoryViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.admin_user = User.objects.create_superuser(username='admin', email='admin@example.com', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.list_url = reverse('api-v1:category-list')
        self.detail_url = reverse('api-v1:category-detail', kwargs={'slug': self.category.slug})

    def test_list_categories(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_category(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_category_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'New Category'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_category_as_user(self):
        self.client.force_authenticate(user=self.user)
        data = {'name': 'New Category'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_category_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Updated Category'}
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_category_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ProductViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product', price=10, stock=5, category=self.category, user=self.user1,
            weight=1, length=1, width=1, height=1
        )
        self.list_url = reverse('api-v1:product-list')
        self.detail_url = reverse('api-v1:product-detail', kwargs={'slug': self.product.slug})

    def test_list_products(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_product(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_product(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'name': 'New Product', 'description': 'A new product', 'price': 20.00, 'stock': 10,
            'category': self.category.slug, 'weight': 1, 'length': 1, 'width': 1, 'height': 1
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_product_by_owner(self):
        self.client.force_authenticate(user=self.user1)
        data = {'name': 'Updated Product', 'price': 15.00}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product')

    def test_update_product_by_other_user(self):
        self.client.force_authenticate(user=self.user2)
        data = {'name': 'Updated Product'}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_product_by_owner(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ReviewViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product', price=10, stock=5, category=self.category, user=self.user1,
            weight=1, length=1, width=1, height=1
        )
        self.order = Order.objects.create(user=self.user1)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)
        self.review = Review.objects.create(product=self.product, user=self.user1, rating=5, comment='Great!')
        self.list_url = reverse('api-v1:product-reviews-list', kwargs={'product_slug': self.product.slug})
        self.detail_url = reverse('api-v1:product-reviews-detail', kwargs={'product_slug': self.product.slug, 'pk': self.review.pk})

    def test_list_reviews(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_review_by_purchaser(self):
        self.client.force_authenticate(user=self.user1)
        # Need to delete the existing review to create a new one
        self.review.delete()
        # Mark the order as completed to allow review
        self.order.status = Order.Status.PAID
        self.order.save()
        data = {'rating': 4, 'comment': 'Good product.'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_create_review_by_non_purchaser(self):
        self.client.force_authenticate(user=self.user2)
        data = {'rating': 3, 'comment': 'I dont know.'}
        response = self.client.post(self.list_url, data)
        # The view checks if a user has a COMPLETED order. Let's make sure that check works.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
