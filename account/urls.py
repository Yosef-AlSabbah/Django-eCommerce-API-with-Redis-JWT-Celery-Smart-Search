from django.urls import path

# Import views for user management and authentication
from .views import (
    UserViewSet,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenDestroyView, ActivateView,
)

# Application namespace to avoid conflicts
app_name = 'auth'

# Define actions for UserViewSet
user_create = UserViewSet.as_view({'post': 'create'})
user_activate = UserViewSet.as_view({'post': 'activation'})
user_set_password = UserViewSet.as_view({'post': 'set_password'})
user_reset_password = UserViewSet.as_view({'post': 'reset_password'})
user_reset_password_confirm = UserViewSet.as_view({'post': 'reset_password_confirm'})

urlpatterns = [
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ AUTHENTICATION URLS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # User registration
    path('register/', user_create, name='register'),

    # User activation
    path('activate/', user_activate, name='activate'),
    path('activate/<str:uid>/<str:token>/', ActivateView.as_view(), name='activate-form'),

    # Set password
    path('set-password/', user_set_password, name='set_password'),

    # Reset password
    path('reset-password/', UserViewSet.as_view({'post': 'reset_password'}), name='reset_password'),

    # Confirm password reset
    path('reset-password-confirm/', user_reset_password_confirm, name='reset_password_confirm'),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ USER Authentication URLS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Obtain a new JWT token
    path('token/create/', TokenObtainPairView.as_view(), name='jwt-create'),

    # Refresh an existing JWT token
    path('token/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),

    # Verify an existing JWT token
    path('token/verify/', TokenVerifyView.as_view(), name='jwt-verify'),

    # Destroy an existing JWT token
    path('token/destroy/', TokenDestroyView.as_view(), name='jwt-destroy'),
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ USER MANAGEMENT URLS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Current authenticated user endpoint with multiple HTTP methods
    path(
        'me/',
        UserViewSet.as_view({'get': 'me', 'put': 'me', 'patch': 'me', 'delete': 'me'}),
        name='current_user'
    ),
    path('staff-check/', UserViewSet.as_view({'get': 'staff_check'}), name='staff_check'),
]

