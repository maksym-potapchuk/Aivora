from .base import models, uuid
from .abs import AbstractTimeStampModel
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from .choice import UserRoleChoice, UserRankChoice


class CustomUserManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, password, country, **kwargs):
        if not email:
            raise ValueError("Provide Email field")

        email = self.normalize_email(email=email)

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            country=country,
            **kwargs
        )
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, first_name, last_name, email, password, country, **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_email_verified", True)

        return self.create_user(first_name, last_name, email, password, country, **kwargs)


class User(AbstractBaseUser, AbstractTimeStampModel, PermissionsMixin):
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    first_name = models.CharField(max_length=32, verbose_name="First name")
    last_name = models.CharField(max_length=32, verbose_name="Second name")
    email = models.EmailField(max_length=64, unique=True, verbose_name="Email")
    phone = models.CharField(max_length=13, blank=True, null=True, verbose_name="Phone number", unique=True)
    country = models.CharField(max_length=32, verbose_name="Country")
    city = models.CharField(max_length=32, verbose_name="City/Town", blank=True, null=True)
    photo = models.ImageField(upload_to="profiles_img/", blank=True, null=True)
    appointment = models.CharField(verbose_name="Appointment", blank=True, null=True)
    rank = models.CharField(
        verbose_name="Rank",
        choices=UserRankChoice.choices,
        default=UserRankChoice.NOOB,
        blank=True, null=True
    )
    experience = models.PositiveIntegerField(verbose_name="Experience points", default=0)
    role = models.CharField(
        verbose_name="Role",
        choices=UserRoleChoice.choices,
        default=UserRoleChoice.STUDENT,
    )
    is_email_verified = models.BooleanField(default=False, verbose_name="Veryfied Email")
    last_logined = models.DateTimeField(null=True, blank=True, verbose_name="Last logined at")

    is_active = models.BooleanField(
        default=False, verbose_name="Is active user",
        help_text="If true allows user login into system"
    )
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "country"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"