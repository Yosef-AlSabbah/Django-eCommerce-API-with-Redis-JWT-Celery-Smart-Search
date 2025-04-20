import markdown
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy

from .models import Product


class TrendingProductsFeed(Feed):
    title = 'eCommerce API - Trending'
    link = reverse_lazy('api-v1:products-list')
    description = 'Trending Products for this week'

    def items(self):
        return Product.in_stock.all()[:5]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return truncatewords_html(markdown.markdown(item.description), 30)

    def item_pubdate(self, item):
        return item.updated
