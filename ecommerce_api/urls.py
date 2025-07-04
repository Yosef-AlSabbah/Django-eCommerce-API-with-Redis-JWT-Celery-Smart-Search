"""
URL configuration for ecommerce_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import JsonResponse
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from shop.feeds import TrendingProductsFeed
from shop.sitemaps import ProductSitemap

sitemaps = {
    'products': ProductSitemap,
}


@require_http_methods(["GET"])
def api_root(request):
    """Root API endpoint that provides information about available endpoints"""
    return JsonResponse({
        'message': 'E-commerce API',
        'version': '1.0',
        'status': 'healthy',
        'endpoints': {
            'auth': '/auth/',
            'api': '/api/v1/',
            'admin': '/admin/',
            'payment': '/payment/',
            'docs': '/api/schema/swagger-ui/',
        }
    })


urlpatterns = [
    path('', api_root, name='api-root'),  # Handle root path requests
    path('auth/', include('account.urls', namespace='auth')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/', include('api.urls', namespace='api-v1')),
    path('payment/', include('payment.urls', namespace='payment')),
    path('admin/', admin.site.urls),
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    path('feed/', TrendingProductsFeed(), name='product-feed'),
    path('social-auth/', include('social_django.urls', namespace='social')),
]

urlpatterns += debug_toolbar_urls()

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
