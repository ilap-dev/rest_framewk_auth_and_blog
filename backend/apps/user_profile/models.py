import uuid
from django.db import models
from ckeditor.fields import RichTextField
from django.conf import settings
from djoser.signals import user_registered, user_activated
from ..media.models import Media

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


#def post_user_registered(user, *args, **kwargs):
#    print("User has registered")

def post_user_activated(user, *args, **kwargs):
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

#user_registered.connect(post_user_registered)
user_activated.connect(post_user_activated)