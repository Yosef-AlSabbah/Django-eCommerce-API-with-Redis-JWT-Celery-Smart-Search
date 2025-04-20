from django.urls import path

from . import views

urlpatterns = [
    path(
        'chat/<uuid:product_id>/',
        views.ProductChatAPIView.as_view(),
        name='chat',
    )
]
