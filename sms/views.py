from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .providers import SmsIrProvider
from .models import OTPCode
import random
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RequestOTP(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        code = random.randint(100000, 999999)
        expires_at = timezone.now() + timedelta(minutes=5)
        OTPCode.objects.create(phone=phone, code=code, expires_at=expires_at)

        provider = SmsIrProvider()
        # You should get the template ID from settings
        from django.conf import settings
        template_id = settings.SMS_IR_OTP_TEMPLATE_ID
        response = provider.send_otp(phone, code, template_id)

        if response.get('error'):
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)


class VerifyOTP(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        code = request.data.get('code')
        if not phone or not code:
            return Response({'error': 'Phone and code are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp = OTPCode.objects.get(phone=phone, code=code, used=False, expires_at__gte=timezone.now())
        except OTPCode.DoesNotExist:
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

        otp.used = True
        otp.save()

        user, created = User.objects.get_or_create(phone_number=phone)
        if created:
            # You might want to set a dummy email or handle user creation more gracefully
            user.email = f'{phone}@example.com'
            user.set_unusable_password()
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
