import environ
from datetime import timedelta
from pathlib import Path

from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']  # Allow all hosts in development - restrict in production

# CSRF_TRUSTED_ORIGINS = [
#     'http://localhost:3000'
# ]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = ['csrftoken', 'sessionid']

# Application definition
#      ╭──────────────────────────────────────────────────────────╮
#      │                Application Configuration                 │
#      ╰──────────────────────────────────────────────────────────╯
# ───── Defines The Core, Third-party, And Custom Applications Used In The Project ─────

# Core Django applications provided by the framework
DJANGO_APPS = [
    'django.contrib.admin',  # Admin interface for managing the application
    'django.contrib.auth',  # Authentication framework
    'django.contrib.contenttypes',  # Content type system for permissions
    'django.contrib.sessions',  # Session framework
    'django.contrib.messages',  # Messaging framework
    'django.contrib.sites',  # Multi-site support
    'django.contrib.sitemaps',  # Sitemap generation
    'django.contrib.staticfiles',  # Static file management
    'django.contrib.postgres',  # PostgreSQL-specific features
]

# Third-party applications installed via pip
THIRD_PARTY_APPS = [
    'taggit',  # Tagging library for Django
    'drf_spectacular',  # OpenAPI schema generation for Django REST Framework
    'debug_toolbar',  # Debugging tool for development
    'django_filters',  # Filtering support for Django REST Framework
    'rest_framework',  # Django REST Framework for building APIs
    'rest_framework.authtoken',  # Token-based authentication for REST Framework
    'django_redis',  # Redis cache backend
    'social_django',  # Social authentication (e.g., Google, Facebook)
    'djoser',  # User authentication and management
    'simple_history',  # Track changes to model instances
    'django_extensions',  # Additional management commands and utilities
    'rest_framework_simplejwt.token_blacklist',  # JWT token blacklist for security
    'corsheaders'  # Cross-Origin Resource Sharing (CORS) headers
]

# Custom applications developed for this project
CUSTOM_APPS = [
    'api.apps.ApiConfig',  # API application
    'shop.apps.ShopConfig',  # Shop application for managing products
    'cart.apps.CartConfig',  # Cart application for managing shopping carts
    'orders.apps.OrdersConfig',  # Orders application for managing customer orders
    'coupons.apps.CouponsConfig',  # Coupons application for discounts

    'chat.apps.ChatConfig',  # Chat application for real-time communication
    'payment.apps.PaymentConfig',  # Payment application for processing transactions
    'account.apps.AccountConfig',  # Account application for user management
    'shipping.apps.ShippingConfig',
    'sms.apps.SmsConfig',
]

# Combine all applications into the INSTALLED_APPS setting
INSTALLED_APPS = ['daphne'] + DJANGO_APPS + THIRD_PARTY_APPS + CUSTOM_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'cart.middleware.CartSessionMiddleware',  # Add custom cart session middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce_api.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
#      ╭──────────────────────────────────────────────────────────╮
#      │                  Database Configuration                  │
#      ╰──────────────────────────────────────────────────────────╯
# ──────── This Section Configures The Database Connection For The Application ─────────
DATABASES = {
    'default': env.db(),
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Additional locations of static files
# STATICFILES_DIRS = [
#     BASE_DIR / 'static',
# ]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'account.UserAccount'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

#      ╭──────────────────────────────────────────────────────────╮
#      │                 Framework Configuration                  │
#      ╰──────────────────────────────────────────────────────────╯
# ────────────── Settings For Authentication, Pagination, And Throttling ───────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'EXCEPTION_HANDLER': 'ecommerce_api.core.exceptions.custom_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'ecommerce_api.utils.pagination.CustomPageNumberPagination',
    'DEFAULT_RENDERER_CLASSES': [
        'ecommerce_api.core.renderers.ApiResponseRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '400/day',
        'user': '1000/day',
    },
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

#      ╭──────────────────────────────────────────────────────────╮
#      │       Configuration for JWT Authentication Tokens        │
#      ╰──────────────────────────────────────────────────────────╯
# ━━ THIS SECTION SETS THE DURATION FOR BOTH ACCESS AND REFRESH TOKENS IN THE APPLICATION, USING THE SIMPLE_JWT SETTINGS. ━━
SIMPLE_JWT = {
    # Sets the lifespan of the access token.
    # After 15 minutes, the access token will expire, requiring the user to use the refresh token to obtain a new access token.
    'ACCESS_TOKEN_LIFETIME': timedelta(days=15),

    # Sets the lifespan of the refresh token.
    # After 7 days, the refresh token will expire, requiring the user to re-authenticate to get a new refresh token.
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Defines the class used for authentication tokens, specifying AccessToken here
    # as the type of token used by Simple JWT.
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),

    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

#      ╭──────────────────────────────────────────────────────────╮
#      │                API Documentation Settings                │
#      ╰──────────────────────────────────────────────────────────╯
# ─────────────── Configure Openapi Schema For A Scalable Ecommerce Api ────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Hypex eCommerce API Documentation",
    "DESCRIPTION": "A scalable RESTful eCommerce API using Django, JWT auth, Redis caching, Celery for task scheduling, advanced search, tagging, and personalized results.",
    "VERSION": "1.2.6",
    "SERVE_INCLUDE_SCHEMA": True,  # Enables schema serving at runtime
    "SCHEMA_PATH_PREFIX": "/api/v1",  # Filter paths for the documented schema

    # Enforce strict validation and clean documentation
    "SORT_OPERATIONS": True,  # Sort operations alphabetically by path and method
    "SORT_SCHEMA_BY_TAGS": True,  # Sort schema tags alphabetically
    "ENUM_NAME_OVERRIDES": {},  # Customize enum names if needed
    "COMPONENT_SPLIT_REQUEST": False,  # Avoid splitting components for requests and responses unnecessarily

    # Ensure compatibility with DELETE methods accepting body payloads
    "ENABLE_DELETE_METHODS_WITH_BODY": True,
    # "ENABLE_DELETE_METHODS_WITH_BODY": False,

    # Tags and grouping
    "TAGS": [
        {
            "name": "User Management",
            "description": "Endpoints for managing user profiles, accounts, and related data."
        },
        {
            "name": "User Authentication",
            "description": "Endpoints for user login, logout, and authentication."
        },
        {
            "name": "Payments",
            "description": "Endpoints for processing and managing payments."
        },
        {
            "name": "Orders",
            "description": "Endpoints for managing customer orders and order details."
        },
        {
            "name": "Coupons",
            "description": "Endpoints for creating and managing discount coupons."
        },
        {
            "name": "Categories",
            "description": "Endpoints for managing product categories."
        },
        {
            "name": "Chat",
            "description": "Endpoints for real-time communication and chat functionality."
        },
        {
            "name": "Cart",
            "description": "Endpoints for managing the shopping cart."
        },
        {
            "name": "Reviews",
            "description": "Endpoints for managing product reviews."
        }
    ],
    # Authentication configuration
    "SECURITY": [
        {"bearerAuth": []},  # Assuming you're using Bearer/Token-based authentication
    ],

    # Deprecation warnings
    "APPEND_PATH_TO_TAGS": False,  # Do not append path to tags; keeps tags clean
    "SCHEMA_EXTENSIONS": [],  # Add custom schema extensions if needed
}

#      ╭──────────────────────────────────────────────────────────╮
#      │                 Configure Redis Caching                  │
#      ╰──────────────────────────────────────────────────────────╯
# ──────────────── Set Up Redis As The Default Cache Backend For Django ────────────────
CACHES = {
    "default": env.cache('REDIS_URL')
}

#      ╭──────────────────────────────────────────────────────────╮
#      │           Configure Redis for Django Channels            │
#      ╰──────────────────────────────────────────────────────────╯
#  Configure Django Channels With Redis For Real-time Communication And Asynchronous Task Handling
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL')],
        },
    },
}

# Django Debug Toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

CART_SESSION_ID = 'cart'

#      ╭──────────────────────────────────────────────────────────╮
#      │                   Email Configuration                    │
#      ╰──────────────────────────────────────────────────────────╯
# ━━ THIS SECTION CONFIGURES THE EMAIL BACKEND FOR SENDING EMAILS IN THE APPLICATION. ━━
EMAIL_CONFIG = env.email_url('EMAIL_URL')
vars().update(EMAIL_CONFIG)

SITE_ID = 1

ASGI_APPLICATION = 'ecommerce_api.asgi.application'

SMS_IR_OTP_TEMPLATE_ID = env('SMS_IR_OTP_TEMPLATE_ID', default=123456)

POSTEX_SENDER_NAME = env('POSTEX_SENDER_NAME', default='Your Company Name')
POSTEX_SENDER_PHONE = env('POSTEX_SENDER_PHONE', default='Your Company Phone')
POSTEX_SENDER_ADDRESS = env('POSTEX_SENDER_ADDRESS', default='Your Company Address')
POSTEX_SENDER_POSTAL_CODE = env('POSTEX_SENDER_POSTAL_CODE', default='Your Company Postal Code')
POSTEX_FROM_CITY_CODE = env.int('POSTEX_FROM_CITY_CODE', default=1)
POSTEX_SERVICE_TYPE = env('POSTEX_SERVICE_TYPE', default='standard')

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.google.GoogleOAuth2',
]
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('GOOGLE_OAUTH2_SECRET')

DJOSER = {
    'HIDE_USERS': True,
    'EMAIL': {
        'activation': 'account.emails.CustomActivationEmail',  # Path to your custom class
    },
    # Specifies the custom serializers
    'SERIALIZERS': {
        'user_create': 'users.api.serializers.UserProfileSerializer',  # Register user with profile
        'user_delete': 'djoser.serializers.UserDeleteSerializer',
    },
    'LOGIN_FIELD': 'email',  # Use email for login instead of username
    'SEND_ACTIVATION_EMAIL': True,  # Send activation email upon registration
    'SEND_CONFIRMATION_EMAIL': True,  # Send confirmation email for actions like password changes
    'ACTIVATION_URL': 'auth/activate/{uid}/{token}',  # URL endpoint for account activation

    # URL endpoints for password reset and username reset confirmations
    'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
    'USERNAME_RESET_CONFIRM_URL': 'username/reset/confirm/{uid}/{token}',

    'PASSWORD_RESET_SHOW_EMAIL': True,  # Show email in the password reset form
    'USERNAME_CHANGED_EMAIL_CONFIRMATION': True,  # Send confirmation email if username is changed
    'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,  # Send confirmation email if password is changed

    # Require password retype during user creation for verification
    'USER_CREATE_PASSWORD_RETYPE': True,
}

LOGIN_URL = reverse_lazy('auth:jwt-create')
USERNAME_FIELD = 'email'

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}",
        }
    },
    'USE_SESSION_AUTH': False,
}

DOMAIN = env('DOMAIN')
SITE_NAME = env('SITE_NAME')

TAGGIT_CASE_INSENSITIVE = True

# Celery Configuration using Redis
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Session cookie settings - Fixed for admin compatibility
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True  # Changed to True for security and admin compatibility
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True  # Ensure sessions are saved on every request

# CSRF settings - Updated for better compatibility
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False  # Explicitly set for compatibility
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',  # Added for admin access
]
