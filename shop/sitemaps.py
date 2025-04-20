from django.contrib.sitemaps import Sitemap

from .models import Product


class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Product.in_stock.all()

    def lastmod(self, obj):
        return obj.updated
