from logging import getLogger

from django.shortcuts import render
from django.views import View
from djoser.views import UserViewSet as BaseUserViewSet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseTokenObtainPairView,
    TokenRefreshView as BaseTokenRefreshView,
    TokenVerifyView as BaseTokenVerifyView, TokenBlacklistView,
)

from .models import Profile
from .serializers import UserProfileSerializer, RefreshTokenSerializer

logger = getLogger(__name__)


class UserViewSet(BaseUserViewSet):
    """
    View for managing user actions including profile operations and authentication flows.
    """

    @extend_schema(
        operation_id="user_me_retrieve",
        description="Retrieve the authenticated user's profile.",
        tags=["User Management"],
        methods=['GET'],
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Invalid request."),
        }
    )
    @extend_schema(
        operation_id="user_me_update",
        description="Update the authenticated user's profile.",
        tags=["User Management"],
        methods=['PUT'],
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Invalid request."),
        }
    )
    @extend_schema(
        operation_id="user_me_partial_update",
        description="Partially update the authenticated user's profile.",
        tags=["User Management"],
        methods=['PATCH'],
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Invalid request."),
        }
    )
    @extend_schema(
        operation_id="user_me_delete",
        description="Delete the authenticated user's profile.",
        tags=["User Management"],
        methods=['DELETE'],
        responses={
            204: OpenApiResponse(description="No Content"),
            400: OpenApiResponse(description="Invalid request."),
        }
    )
    @action(detail=False, methods=['get', 'put', 'patch', 'delete'])
    def me(self, request, *args, **kwargs):
        """
        Manage operations on the authenticated user's profile.
        """
        try:
            # Get the user's profile for serialization
            profile, created = Profile.objects.get_or_create(user=request.user)

            if request.method == "GET":
                serializer = UserProfileSerializer(profile, context={'request': request})
                return Response({
                    "message": "Profile retrieved",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)

            elif request.method in ["PUT", "PATCH"]:
                partial = request.method == "PATCH"
                serializer = UserProfileSerializer(
                    profile, data=request.data, partial=partial, context={'request': request}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()  # This calls the update method on the serializer
                return Response({
                    "message": "Profile updated",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)

            elif request.method == "DELETE":
                user = request.user
                user.delete()
                return Response({
                    "message": "Profile deleted"
                }, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error during profile management: {e}", exc_info=True)
            raise  # Let the exception handler deal with it

    @extend_schema(
        operation_id="user_register",
        description="Register a new user account.",
        tags=["User Authentication"],
        methods=['POST'],
        responses={
            201: OpenApiResponse(
                description="User successfully registered. Please check your email to activate your account."),
            400: OpenApiResponse(description="Invalid request."),
            500: OpenApiResponse(description="An internal error occurred."),
        }
    )
    def create(self, request, *args, **kwargs):
        """
        Handle POST requests to create a new user account.
        """
        try:
            response = super().create(request, *args, **kwargs)
            return Response({
                "message": "User successfully registered. Please check your email to activate your account.",
                "data": response.data
            }, status=response.status_code)
        except Exception as e:
            logger.error(f"Error during user registration: {e}", exc_info=True)
            raise

    @extend_schema(
        operation_id="user_activate",
        description="Activate a user account using the activation key.",
        tags=["User Authentication"],
        methods=['POST'],
        responses={
            200: OpenApiResponse(description="Account successfully activated."),
            400: OpenApiResponse(description="Invalid activation key."),
        }
    )
    def activation(self, request, *args, **kwargs):
        """
        Activate a user account using the activation key.
        """
        try:
            response = super().activation(request, *args, **kwargs)
            return Response({
                "message": "Account successfully activated",
                "data": response.data
            }, status=response.status_code)
        except Exception as e:
            logger.error(f"Error during account activation: {e}", exc_info=True)
            raise

    @extend_schema(
        operation_id="user_set_password",
        description="Set a new password for the authenticated user.",
        tags=["User Management"],
        methods=['POST'],
        responses={
            200: OpenApiResponse(description="Password successfully updated."),
            400: OpenApiResponse(description="Invalid password input."),
        }
    )
    def set_password(self, request, *args, **kwargs):
        """
        Set a new password for the authenticated user.
        """
        try:
            response = super().set_password(request, *args, **kwargs)
            return Response({
                "message": "Password successfully updated",
                "data": response.data
            }, status=response.status_code)
        except Exception as e:
            logger.error(f"Error during password update: {e}", exc_info=True)
            raise

    @extend_schema(
        operation_id="user_reset_password",
        description="Initiate a password reset request.",
        tags=["User Management"],
        methods=['POST'],
        responses={
            200: OpenApiResponse(description="Password reset email sent."),
            400: OpenApiResponse(description="Invalid email address."),
        }
    )
    def reset_password(self, request, *args, **kwargs):
        """
        Initiate a password reset request.
        """
        try:
            response = super().reset_password(request, *args, **kwargs)
            return Response({
                "message": "Password reset email sent",
                "data": response.data
            }, status=response.status_code)
        except Exception as e:
            logger.error(f"Error during password reset request: {e}", exc_info=True)
            raise

    @extend_schema(
        operation_id="user_reset_password_confirm",
        description="Confirm a password reset using the token and new password.",
        tags=["User Management"],
        methods=['POST'],
        responses={
            200: OpenApiResponse(description="Password successfully reset."),
            400: OpenApiResponse(description="Invalid token or password."),
        }
    )
    def reset_password_confirm(self, request, *args, **kwargs):
        """
        Confirm a password reset using the token and new password.
        """
        try:
            response = super().reset_password_confirm(request, *args, **kwargs)
            return Response({
                "message": "Password successfully reset",
                "data": response.data
            }, status=response.status_code)
        except Exception as e:
            logger.error(f"Error during password reset confirmation: {e}", exc_info=True)
            raise

    @extend_schema(
        operation_id="user_staff_check",
        description="Check if the authenticated user has staff privileges.",
        tags=["User Management"],
        responses={
            200: OpenApiResponse(description="Staff status retrieved successfully."),
            401: OpenApiResponse(description="Authentication required."),
        }
    )
    @action(detail=False, methods=['get'])
    def staff_check(self, request):
        """
        Check if the authenticated user is a staff member.
        """
        try:
            is_staff = request.user.is_staff
            return Response({
                "is_staff": is_staff,
                "message": f"User {'is' if is_staff else 'is not'} a staff member"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error checking staff status: %s", e, exc_info=True)
            return Response({
                "error": "Unable to check staff status"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TokenObtainPairView(BaseTokenObtainPairView):
    """
    Handle POST requests to obtain a new pair of access and refresh tokens.
    """

    @extend_schema(
        operation_id="token_obtain",
        description="Obtain a new pair of access and refresh tokens.",
        tags=["User Authentication"],
        responses={
            200: OpenApiResponse(description="Token successfully obtained."),
            400: OpenApiResponse(description="Invalid credentials."),
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return Response({
                "message": "Token successfully obtained",
                "data": response.data
            }, status=response.status_code)
        except Exception as e:
            logger.error(f"Error during token obtain: {e}", exc_info=True)
            raise


class TokenRefreshView(BaseTokenRefreshView):
    """
    Handle POST requests to refresh an access token using a refresh token.
    """

    @extend_schema(
        operation_id="token_refresh",
        description="Refresh an access token using a refresh token.",
        tags=["User Authentication"],
        responses={
            200: OpenApiResponse(description="Access token successfully refreshed."),
            400: OpenApiResponse(description="Invalid refresh token."),
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return Response({
                "message": "Access token successfully refreshed",
                "data": response.data
            }, status=response.status_code)
        except Exception as e:
            logger.error(f"Error during token refresh: {e}", exc_info=True)
            raise


class TokenVerifyView(BaseTokenVerifyView):
    """
    Verify if an access token is valid.
    """

    @extend_schema(
        operation_id="token_verify",
        description="Verify if an access token is valid.",
        tags=["User Authentication"],
        responses={
            200: OpenApiResponse(description="Token is valid."),
            401: OpenApiResponse(description="Token is invalid or expired."),
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return Response({
                "message": "Token is valid",
                "data": response.data
            }, status=response.status_code)
        except Exception as e:
            logger.error(f"Error during token verification: {e}", exc_info=True)
            raise


class TokenDestroyView(TokenBlacklistView):
    """
    Log out the user by blacklisting their refresh token.
    """
    serializer_class = RefreshTokenSerializer

    @extend_schema(
        operation_id="logout_user",
        description="Log out the user by blacklisting their refresh token.",
        tags=["User Authentication"],
        request=RefreshTokenSerializer,
        responses={
            205: OpenApiResponse(description="Successfully logged out"),
            400: OpenApiResponse(description="Invalid Token"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                "message": "Successfully logged out"
            }, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.error(f"Error during logout: {e}", exc_info=True)
            raise


class ActivateView(View):
    def get(self, request, uid, token):
        return render(
            request,
            'account/activate.html',
            {
                'uid': uid,
                'token': token,
            }
        )

