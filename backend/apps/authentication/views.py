from django.shortcuts import render
# Create your views here.
from rest_framework_api.views import StandardAPIView
from rest_framework import permissions, status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from core.permissions import HasValidAPIKey
from django.utils import timezone
from io import BytesIO
import pyotp
import qrcode

from utils.ip_utils import get_client_ip

User = get_user_model()

class GenerateQRCodeView(StandardAPIView):
    permissions_classes = [permissions.IsAuthenticated, HasValidAPIKey]

    def get(self, request, *args, **kwargs):
        user = request.user
        email = user.email
        otp_base32 = pyotp.random_base32()
        otp_auth_url = pyotp.totp.TOTP(otp_base32).provisioning_uri(
            name=email.lower(), issuer_name="Django_Auth"
        )

        stream = BytesIO()
        image = qrcode.make(f"{otp_auth_url}")
        image.save(stream)

        user.otp_base32 = otp_base32
        user.qr_code = ContentFile(
            stream.getvalue(), name=f"qr{get_random_string(10)}.png"
        )

        user.save()
        qr_code = user.qr_code
        return self.response(qr_code.url)


class OTPLoginResetView(StandardAPIView):
    permissions_classes = [permissions.IsAuthenticated, HasValidAPIKey]
    def post(self, request, *args, **kwargs):
        user = request.user
        new_ip = get_client_ip(request)

        if user.login_ip and user.login_ip != new_ip:
            print(f"New Login Ip for user: {user.email}")
            #TODO: Send user email
        user.login_ip = new_ip

        if user.qr_code is None or user.otp_base32 is None:
            return self.error("QR Code or OTP Base32 not found for user")

        try:
            totp = pyotp.TOTP(user.otp_base32).now()
        except Exception as e:
            return self.error(f"Error generationg TOPT: {str(e)}")

        user.login_otp = make_password(totp)
        user.otp_created_at = timezone.now()
        user.login_otp_used = False
        user.save()

        return self.response("OTP Reser Succesfully for user")

class VerifyOTPView(StandardAPIView):
    permissions_classes = [permissions.IsAuthenticated, HasValidAPIKey]
    def post(self, request, *args, **kwargs):
        user = request.user

        if user.qr_code is None or user.otp_base32 is None:
            return self.error("QR Code or OTP Base32 not found for user")

        totp = pyotp.TOTP(user.otp_base32)
        otp = request.data.get("otp")
        verified = totp.verify(otp)

        if verified:
            user.login_otp_used = True
            user.save()
            return self.response("OTP Verified")
        else:
            return self.error("Error Verifying One Time Password")


class DisabledOTPView(StandardAPIView):
    permissions_classes = [permissions.IsAuthenticated, HasValidAPIKey]

    def post(self, request, *args, **kwargs):
        user = request.user

        if user.qr_code is None or user.otp_base32 is None:
            return self.error("QR Code or OTP Base32 not found for user")

        totp = pyotp.TOTP(user.otp_base32)
        otp = request.data.get("otp")
        verified = totp.verify(otp)

        if verified:
            user.two_factor_enabled = False
            user.otpauth_url = None
            user.otp_base32 = None
            user.qr_code = None
            user.login_otp = None
            user.login_otp_used = False
            user.otp_created_at = None
            user.save()
            return self.response("Two Factor Authentication Disabled")
        else:
            return self.error("Error Verifying One Time Password")

class Set2FAView(StandardAPIView):
    permissions_classes = [permissions.IsAuthenticated, HasValidAPIKey]

    def post(self, request, *args, **kwargs):
        user = request.user

        if user.qr_code is None:
            return self.error(
                "QR Code not found for user."
            )
        boolean = bool(request.data.get("bool"))

        if boolean:
            user.two_factor_enabled = True
            user.save()
            return self.response("2FA Activated")
        else:
            user.two_factor_enabled = False
            user.save()
            return self.response("2FA Disabled")



class OTPLoginView(StandardAPIView):
    permission_classes = [HasValidAPIKey]
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        otp_code = request.data.get('otp')
        if not email or not otp_code:
            return self.error("Both email and OTP code are required.")

        try:
            user = User.objects.get(email=email)
            totp = pyotp.TOTP(user.otp_base32)
            if not totp.verify(otp_code):
                return self.error("Invalid OTP Code.")

            user.login_otp_used = True
            user.save()

            refresh = RefreshToken.for_user(user)
            return self.response({
                "access":str(refresh.access_token),
                "refresh":str(refresh)
            })
        except User.DoesNotExist:
            return self.response("User does not exist", status=status.HTTP_404_NOT_FOUND)