import uuid
from email.policy import default

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)
# Create your models here.

class UserAccountManager(BaseUserManager):
    RESTRICTED_USERNAMES = ["admin","undefined","null","superuser", "root", "system"]

    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError("Users must have an email address.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)

        first_name = extra_fields.get("first_name", None)
        last_name = extra_fields.get("last_name", None)

        if not first_name or not last_name:
            raise ValueError("Users must have a first name and last name")

        user.first_name = first_name
        user.last_name = last_name

        username =  extra_fields.get("username", None)
        if username and username.lower() in self.RESTRICTED_USERNAMES:
            raise ValueError(f"The username '{username}' is not allowed")

        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email,password,**extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user


class UserAccount(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    email = models.EmailField(unique=True)
    username =models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    update_at = models.DateTimeField(auto_now=True)

    two_factor_enabled = models.BooleanField(default=False)
    otpauth_url= models.CharField(max_length=225, blank=True, null=True)
    otp_base32= models.CharField(max_length=225, null=True)
    qr_code= models.ImageField(upload_to="qrcode/", blank=True, null=True)
    login_otp=models.CharField(max_length=225, blank=True, null=True)
    login_otp_used = models.BooleanField(default=False)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    login_ip = models.CharField(max_length=225, blank=True, null=True)

    objects = UserAccountManager() #Describe el administrador del modelo

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username","first_name","last_name"]

    def __str__(self):
        return self.email

    def get_qr_code(self):
        if self.qr_code and hasattr(self.qr_code, "url"):
            return self.qr_code.url
        return None






