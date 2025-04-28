from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'product', 'sent_at', 'content_preview')
    list_filter = ('sent_at', 'sender', 'recipient', 'product')
    search_fields = ('sender__username', 'recipient__username', 'product__name', 'content')
    ordering = ('-sent_at',)
    date_hierarchy = 'sent_at'

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Message Preview'
