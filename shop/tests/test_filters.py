from django.contrib.auth import get_user_model
from django.test import TestCase
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.test import APIRequestFactory

from shop.filters import ProductFilter, InStockFilterBackend, ProductSearchFilterBackend
from shop.models import Category, Product
from shop.serializers import ProductSerializer


# A dedicated view for testing the ProductFilter (django-filter)
class ProductFilterTestView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter


# A dedicated view for testing the ProductSearchFilterBackend
class ProductSearchTestView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [ProductSearchFilterBackend]


# A dedicated view for testing the InStockFilterBackend
class InStockTestView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [InStockFilterBackend]


class FilterTests(TestCase):
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

        cls.factory = APIRequestFactory()

    def test_filter_by_name_exact(self):
        view = ProductFilterTestView.as_view()
        request = self.factory.get('/', {'name__exact': 'Laptop'})
        response = view(request)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Laptop')

    def test_filter_by_name_icontains(self):
        view = ProductFilterTestView.as_view()
        request = self.factory.get('/', {'name__icontains': 'laptop'})
        response = view(request)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Laptop')

    def test_filter_by_price_exact(self):
        view = ProductFilterTestView.as_view()
        request = self.factory.get('/', {'price__exact': 800.00})
        response = view(request)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Smartphone')

    def test_filter_by_price_range(self):
        view = ProductFilterTestView.as_view()
        request = self.factory.get('/', {'price__range': '700,1300'})
        response = view(request)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_category_slug(self):
        view = ProductFilterTestView.as_view()
        request = self.factory.get('/', {'category__slug': 'electronics'})
        response = view(request)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_tags_name(self):
        view = ProductFilterTestView.as_view()
        request = self.factory.get('/', {'tags__name': 'tech'})
        response = view(request)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_stock_gt(self):
        view = ProductFilterTestView.as_view()
        request = self.factory.get('/', {'stock__gt': 5})
        response = view(request)
        self.assertEqual(len(response.data), 2)

    def test_in_stock_filter_backend(self):
        view = InStockTestView.as_view()
        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(len(response.data), 3)

    def test_product_search_filter_backend(self):
        view = ProductSearchTestView.as_view()
        request = self.factory.get('/', {'search': 'programming'})
        response = view(request)
        self.assertEqual(len(response.data), 2)
