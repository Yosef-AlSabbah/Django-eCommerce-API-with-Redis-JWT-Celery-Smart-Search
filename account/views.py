from logging import getLogger
import random
from datetime import timedelta

from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from djoser.views import UserViewSet as BaseUserViewSet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView as BaseTokenObtainPairView,
    TokenRefreshView as BaseTokenRefreshView,
    TokenVerifyView as BaseTokenVerifyView,
)

from sms.models import OTPCode
from sms.providers import SmsIrProvider

from .models import Profile, UserAccount
from .serializers import RefreshTokenSerializer, UserProfileSerializer

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


def generate_otp():
    return str(random.randint(100000, 999999))


class RequestOTP(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=5)

        otp = OTPCode.objects.create(phone=phone, code=otp_code, expires_at=expires_at)

        sms_provider = SmsIrProvider()
        template_id = settings.SMS_IR_OTP_TEMPLATE_ID
        response = sms_provider.send_otp(phone, otp_code, template_id)

        if response.get('status') == 1:
            return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTP(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        code = request.data.get('code')

        if not phone or not code:
            return Response({'error': 'Phone and code are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp = OTPCode.objects.get(phone=phone, code=code, used=False)
        except OTPCode.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

        otp.used = True
        otp.save()

        try:
            user = UserAccount.objects.get(phone_number=phone)
        except UserAccount.DoesNotExist:
            user = UserAccount.objects.create_user(
                email=None,  # Email can be set later
                phone_number=phone,
                password=None
            )
            # You might want to set a flag to indicate that the user needs to complete their profile
            user.is_active = True
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
