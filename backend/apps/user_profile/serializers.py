from rest_framework import serializers
from ..media.serializers import MediaSerializer
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = MediaSerializer()
    banner_picture = MediaSerializer()
    class Meta:
        model = UserProfile
        fields = [
            'profile_picture',
            'banner_picture',
            'biography',
            'birthday',
            'instagram',
            'facebook',
            'youtube',
        ]