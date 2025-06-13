import uuid
from django.db import models
from ckeditor.fields import RichTextField
from django.conf import settings
from djoser.signals import user_registered, user_activated

from ..authentication.models import UserAccount
from ..media.models import Media
from ..media.serializers import MediaSerializer
from django.utils.html import format_html
from django.db.models.signals import post_save
from django.dispatch import receiver

User = settings.AUTH_USER_MODEL

# Create your models here.

class UserProfile(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profile_picture"
    )

    banner_picture = models.ForeignKey(
        Media,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="banner_picture"
    )

    birthday = models.DateField(blank=True, null=True)
    biography = RichTextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    youtube = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)

    def profile_picture_preview(self):
        if self.profile_picture:
            serializer = MediaSerializer(instance=self.profile_picture)
            url = serializer.data.get('url')
            if url:
                return format_html('<img src="{}" style="width: 100px; height: auto; />',url)
        return 'No Profile Picture'

    def banner_picture_preview(self):
        if self.banner_picture:
            serializer = MediaSerializer(instance=self.banner_picture)
            url = serializer.data.get('url')
            if url:
                return format_html('<img src="{}" style="width: 100px; height: auto; />',url)
        return 'No Banner Picture'

    profile_picture_preview.short_description = "Profile Picture Preview"
    banner_picture_preview.short_description = "Banner Picture Preview"


#def post_user_registered(user, *args, **kwargs):
#    print("User has registered")

"""def post_user_activated(user, *args, **kwargs):
    profile = UserProfile.objects.create(user=user)
    profile_picture = Media.objects.create(
        order=1,
        name="user_default_profile.png",
        size="23.9 KB",
        type="png",
        key="media/profiles/default/user_default_profile.png",
        media_type="image"
    )
    profile.profile_picture = profile_picture
    banner_picture = Media.objects.create(
        order=1,
        name="user_default_profile_bg2.png",
        size="435.4 KB",
        type="png",
        key="media/profiles/default/user_default_profile_bg2.png",
        media_type="image"
    )
    profile.profile_picture = profile_picture
    profile.banner_picture = banner_picture
    profile.save()
    print("User has activated")
"""
#user_registered.connect(post_user_registered)
#user_activated.connect(post_user_activated)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea un perfil de usuario automaticamente cuando se crea un usuario
    :param sender: 
    :param instance: 
    :param created: 
    :param kwargs: 
    :return: 
    """
    if created:
        profile = UserProfile.objects.create(user=instance)
        profile_picture = Media.objects.create(
            order=1,
            name="user_default_profile.png",
            size="23.9 KB",
            type="png",
            key="media/profiles/default/user_default_profile.png",
            media_type="image"
        )
        banner_picture = Media.objects.create(
            order=1,
            name="user_default_profile_bg2.png",
            size="435.4 KB",
            type="png",
            key="media/profiles/default/user_default_profile_bg2.png",
            media_type="image"
        )
        profile.profile_picture = profile_picture
        profile.banner_picture = banner_picture
        profile.save()