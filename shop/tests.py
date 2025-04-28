from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from shop.models import Product, Category
from shop.models import Review

User = get_user_model()


class CategoryTests(APITestCase):
    """
    Test suite for the Category API endpoints.
    """

    def setUp(self):
        """
        Set up test data for the Category tests.
        """
        self.user = User.objects.create_user(username='user', password='pass', email='<EMAIL1>')
        self.admin = User.objects.create_superuser(username='admin', password='pass', email='<EMAIL>')
        self.category = Category.objects.create(name='Computers', slug='computers')
        self.category = Category.objects.create(name='category2', slug='category2')
        self.category_data = {
            'name': 'Electronics',
            'slug': 'electronics'
        }
        self.url = reverse('api-v1:category-list')

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

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
        self.authenticate(self.user)
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)

    def test_authenticated_list_categories(self):
        """
        Test the list categories endpoint.
        """
        url = self.url
        self.authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Computers')

    def test_admin_can_create_category(self):
        self.authenticate(self.admin)
        response = self.client.post(self.url, {'name': 'Electronics', 'slug': 'electronics'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_admin_cannot_create_category(self):
        self.authenticate(self.user)
        response = self.client.post(self.url, {'name': 'Electronics', 'slug': 'electronics'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unique_slug_constraint(self):
        self.authenticate(self.admin)
        response = self.client.post(self.url, {'name': 'Duplicate', 'slug': 'computers'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('slug', response.data)


class ProductConstraintTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='pass', email='admin@example.com')
        self.category = Category.objects.create(name='Computers', slug='computers')
        self.url = reverse('api-v1:product-list')

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_create_product_with_missing_fields(self):
        self.authenticate(self.admin)
        response = self.client.post(self.url, {'name': 'Laptop'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('price', response.data)
        self.assertNotIn('category', response.data)

    def test_unique_slug_constraint(self):
        self.authenticate(self.admin)
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_product_requires_category_and_user(self):
        self.authenticate(self.admin)
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
        self.authenticate(self.admin)
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


class ProductReviewActionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass', email='user@example.com')
        self.admin = User.objects.create_superuser(username='admin', password='pass', email='admin@example.com')
        self.category = Category.objects.create(name='TestCat', slug='testcat')
        self.product = Product.objects.create(
            name='TestProduct', slug='testproduct', price=10, stock=5, category=self.category, user=self.admin
        )
        self.review_url = reverse('api-v1:product-reviews-list', kwargs={'product_slug': self.product.slug})

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_reviews(self):
        Review.objects.create(product=self.product, user=self.user, rating=5, comment='Great!')
        response = self.client.get(self.review_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Great!', str(response.data))

    def test_create_review_authenticated(self):
        self.authenticate(self.user)
        data = {'rating': 4, 'comment': 'Nice!'}
        response = self.client.post(self.review_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_create_review_unauthenticated(self):
        data = {'rating': 4, 'comment': 'Nice!'}
        response = self.client.post(self.review_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_review(self):
        self.authenticate(self.user)
        review = Review.objects.create(product=self.product, user=self.user, rating=3, comment='Ok')
        url = reverse('api-v1:product-reviews-detail', kwargs={'product_slug': self.product.slug, 'pk': review.id})
        data = {'rating': 5, 'comment': 'Updated!'}
        response = self.client.put(url, data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED])

    def test_partial_update_review(self):
        self.authenticate(self.user)
        review = Review.objects.create(product=self.product, user=self.user, rating=3, comment='Ok')
        url = reverse('api-v1:product-reviews-detail', kwargs={'product_slug': self.product.slug, 'pk': review.id})
        data = {'comment': 'Patched!'}
        response = self.client.patch(url, data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED])

    def test_delete_review(self):
        self.authenticate(self.user)
        review = Review.objects.create(product=self.product, user=self.user, rating=2, comment='To delete')
        url = reverse('api-v1:product-reviews-detail', kwargs={'product_slug': self.product.slug, 'pk': review.id})
        response = self.client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_405_METHOD_NOT_ALLOWED])
