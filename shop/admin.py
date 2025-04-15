from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category', 'slug')
    list_filter = ('category', 'tags', 'price', 'stock')
    search_fields = ('name', 'description', 'category__name', 'tags__name')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category',)
