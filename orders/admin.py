from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for OrderItem to display items within the Order admin page.
    """
    model = OrderItem
    extra = 3  # Do not show extra empty rows
    readonly_fields = ('price',)  # Display the calculated price as read-only


def order_payment(obj):
    """
    Generates a clickable link to the Stripe payment page for the given order.

    Args:
        obj: The order object containing the Stripe ID and URL.

    Returns:
        str: A safe HTML string with a link to the Stripe payment page if the
        Stripe ID exists, otherwise an empty string.
    """
    url = obj.get_stripe_url()
    if obj.stripe_id:
        html = f'<a href="{url}" target="_blank">{obj.stripe_id}</a>'
        return mark_safe(html)
    return ''


order_payment.short_description = 'Stripe payment'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for managing the Order model in the Django admin interface.

    This class customizes the display, filtering, searching, and ordering of orders,
    and includes inline management of associated OrderItems.
    """
    list_display = ('order_id', 'user', 'status', 'order_date', 'updated', 'total_payable', order_payment)
    list_filter = ('status', 'order_date', 'updated')
    search_fields = ('user__username', 'order_id')
    ordering = ('-order_date',)
    inlines = [OrderItemInline]
    readonly_fields = ('total_payable', 'order_id', 'order_date')  # Make these fields read-only
