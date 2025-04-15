from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for OrderItem to display items within the Order admin page.
    """
    model = OrderItem
    extra = 3  # Do not show extra empty rows
    readonly_fields = ('price',)  # Display the calculated price as read-only


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for managing the Order model in the Django admin interface.

    This class customizes the display, filtering, searching, and ordering of orders,
    and includes inline management of associated OrderItems.
    """
    list_display = ('order_id', 'user', 'status', 'order_date', 'updated', 'total_price')
    list_filter = ('status', 'order_date', 'updated')
    search_fields = ('user__username', 'order_id')
    ordering = ('-order_date',)
    inlines = [OrderItemInline]
    readonly_fields = ('total_price', 'order_id', 'order_date')  # Make these fields read-only
