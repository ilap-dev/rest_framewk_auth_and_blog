from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class UserCreateSerializer(UserCreateSerializer):
    qr_code = serializers.URLField(source="get_qr_code")
    class Meta(UserCreateSerializer.Meta):  # Nota que extiende Meta correctamente
        model = User
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    qr_code = serializers.URLField(source="get_qr_code")
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "update_at",
            "two_factor_enabled",
            "otpauth_url",
            "login_otp",
            "login_otp_used",
            "otp_created_at",
            "qr_code",
        ]

class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "update_at",
        ]


