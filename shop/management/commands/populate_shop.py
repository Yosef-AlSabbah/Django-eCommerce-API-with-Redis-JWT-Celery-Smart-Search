from decimal import Decimal
from urllib.request import urlretrieve

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import BaseCommand

from account.models import Profile
from shop.models import Category, Product

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample categories and products with images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories and products before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing categories and products...')
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data.'))

        # Get or create a user to assign products to
        user = self.get_or_create_user()

        # Create categories
        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
            {'name': 'Clothing', 'description': 'Fashion and apparel'},
            {'name': 'Books', 'description': 'Books and literature'},
            {'name': 'Home & Garden', 'description': 'Home improvement and gardening supplies'},
            {'name': 'Sports & Outdoors', 'description': 'Sports equipment and outdoor gear'},
            {'name': 'Health & Beauty', 'description': 'Health and beauty products'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'name': cat_data['name']}
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')

        # Create products with sample data
        products_data = [
            {
                'name': 'iPhone 15 Pro',
                'description': 'Latest iPhone with advanced camera system and A17 Pro chip.',
                'price': Decimal('999.99'),
                'stock': 50,
                'category': 'Electronics',
                'image_url': 'https://via.placeholder.com/400x400/007bff/ffffff?text=iPhone+15+Pro',
                'tags': ['smartphone', 'apple', 'mobile', 'technology']
            },
            {
                'name': 'MacBook Air M3',
                'description': 'Lightweight laptop with M3 chip for exceptional performance.',
                'price': Decimal('1299.99'),
                'stock': 25,
                'category': 'Electronics',
                'image_url': 'https://via.placeholder.com/400x400/6c757d/ffffff?text=MacBook+Air',
                'tags': ['laptop', 'apple', 'computer', 'productivity']
            },
            {
                'name': 'Wireless Headphones',
                'description': 'Premium noise-cancelling wireless headphones.',
                'price': Decimal('299.99'),
                'stock': 100,
                'category': 'Electronics',
                'image_url': 'https://via.placeholder.com/400x400/28a745/ffffff?text=Headphones',
                'tags': ['audio', 'wireless', 'music', 'headphones']
            },
            {
                'name': 'Cotton T-Shirt',
                'description': 'Comfortable 100% cotton t-shirt in various colors.',
                'price': Decimal('24.99'),
                'stock': 200,
                'category': 'Clothing',
                'image_url': 'https://via.placeholder.com/400x400/dc3545/ffffff?text=T-Shirt',
                'tags': ['clothing', 'cotton', 'casual', 'shirt']
            },
            {
                'name': 'Denim Jeans',
                'description': 'Classic fit denim jeans made from premium denim.',
                'price': Decimal('79.99'),
                'stock': 75,
                'category': 'Clothing',
                'image_url': 'https://via.placeholder.com/400x400/6f42c1/ffffff?text=Jeans',
                'tags': ['clothing', 'denim', 'jeans', 'casual']
            },
            {
                'name': 'Python Programming Book',
                'description': 'Comprehensive guide to Python programming for beginners and experts.',
                'price': Decimal('39.99'),
                'stock': 60,
                'category': 'Books',
                'image_url': 'https://via.placeholder.com/400x400/fd7e14/ffffff?text=Python+Book',
                'tags': ['book', 'programming', 'python', 'education']
            },
            {
                'name': 'JavaScript: The Good Parts',
                'description': 'Essential JavaScript concepts and best practices.',
                'price': Decimal('34.99'),
                'stock': 45,
                'category': 'Books',
                'image_url': 'https://via.placeholder.com/400x400/20c997/ffffff?text=JS+Book',
                'tags': ['book', 'javascript', 'programming', 'web']
            },
            {
                'name': 'Garden Tool Set',
                'description': 'Complete set of essential gardening tools.',
                'price': Decimal('89.99'),
                'stock': 30,
                'category': 'Home & Garden',
                'image_url': 'https://via.placeholder.com/400x400/795548/ffffff?text=Garden+Tools',
                'tags': ['gardening', 'tools', 'outdoor', 'plants']
            },
            {
                'name': 'LED Plant Grow Light',
                'description': 'Full spectrum LED grow light for indoor plants.',
                'price': Decimal('159.99'),
                'stock': 40,
                'category': 'Home & Garden',
                'image_url': 'https://via.placeholder.com/400x400/9c27b0/ffffff?text=Grow+Light',
                'tags': ['lighting', 'plants', 'indoor', 'gardening']
            },
            {
                'name': 'Running Shoes',
                'description': 'Professional running shoes with advanced cushioning.',
                'price': Decimal('129.99'),
                'stock': 80,
                'category': 'Sports & Outdoors',
                'image_url': 'https://via.placeholder.com/400x400/e91e63/ffffff?text=Running+Shoes',
                'tags': ['shoes', 'running', 'sports', 'fitness']
            },
            {
                'name': 'Yoga Mat',
                'description': 'Non-slip yoga mat perfect for all types of yoga practice.',
                'price': Decimal('49.99'),
                'stock': 120,
                'category': 'Sports & Outdoors',
                'image_url': 'https://via.placeholder.com/400x400/607d8b/ffffff?text=Yoga+Mat',
                'tags': ['yoga', 'fitness', 'exercise', 'mat']
            },
            {
                'name': 'Moisturizing Face Cream',
                'description': 'Hydrating face cream with natural ingredients.',
                'price': Decimal('29.99'),
                'stock': 90,
                'category': 'Health & Beauty',
                'image_url': 'https://via.placeholder.com/400x400/ff9800/ffffff?text=Face+Cream',
                'tags': ['skincare', 'beauty', 'moisturizer', 'natural']
            },
        ]

        created_count = 0
        for product_data in products_data:
            category = categories[product_data['category']]

            # Check if product already exists
            if Product.objects.filter(name=product_data['name']).exists():
                self.stdout.write(f'Product already exists: {product_data["name"]}')
                continue

            # Create product
            product = Product.objects.create(
                name=product_data['name'],
                description=product_data['description'],
                price=product_data['price'],
                stock=product_data['stock'],
                category=category,
                user=user
            )

            # Add tags
            if 'tags' in product_data:
                product.tags.add(*product_data['tags'])

            # Download and attach image
            if 'image_url' in product_data:
                try:
                    self.download_image(product, product_data['image_url'])
                    self.stdout.write(f'Downloaded image for: {product.name}')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Failed to download image for {product.name}: {str(e)}')
                    )

            created_count += 1
            self.stdout.write(f'Created product: {product.name}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(categories)} categories and {created_count} products!')
        )

    def get_or_create_user(self):
        """Get or create a user to assign products to."""
        # Try to get an existing superuser
        user = User.objects.filter(is_superuser=True).first()

        if not user:
            # Create a default user if no superuser exists
            user = User.objects.create_user(
                email='admin@example.com',
                username='admin',
                password='admin123',
                first_name='Admin',
                last_name='User',
                is_active=True,
                is_staff=True,
                is_superuser=True
            )

            # Create profile for the user
            Profile.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal('0.0')}
            )

            self.stdout.write(f'Created default admin user: {user.username}')
        else:
            self.stdout.write(f'Using existing user: {user.username}')

        return user

    def download_image(self, product, image_url):
        """Download an image from URL and attach it to the product."""
        try:
            # Create a temporary file
            img_temp = NamedTemporaryFile(delete=True)

            # Download the image
            urlretrieve(image_url, img_temp.name)

            # Create filename
            filename = f"{product.slug}.jpg"

            # Save the image to the product
            product.thumbnail.save(
                filename,
                File(img_temp),
                save=True
            )
        except Exception as e:
            # If download fails, we'll just continue without the image
            self.stdout.write(
                self.style.WARNING(f'Failed to download image: {str(e)}')
            )
