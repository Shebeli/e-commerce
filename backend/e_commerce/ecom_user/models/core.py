from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ecom_core.validators import (
    validate_phone,
    validate_username,
    validate_national_code,
)
from ecom_user.managers import EcomUserManager


class EcomUser(AbstractBaseUser):
    "This model does not contain any superuser or staff attributes as its handled in a seperate model named 'AdminUser'"
    first_name = models.CharField(_("First Name"), max_length=50, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=50, blank=True)
    username = models.CharField(
        _("Username"),
        unique=True,
        help_text=_(
            "Maximum of 40 characters. Only letters, digits and the special character . are allowed"
        ),
        validators=[validate_username],
        error_messages={
            "null": _("The username cannot be null"),
            "blank": _("The username cannot be blank"),
            "unique": _("The username already exists"),
            "invalid": _(
                "The username is invalid. Please refer to username help text."
            ),
        },
        max_length=40,
        blank=True,
    )
    email = models.EmailField(_("Email Address"), blank=True, unique=True)
    phone = models.CharField(
        _("Phone Number"),
        max_length=13,
        validators=[validate_phone],
        unique=True,
        blank=True,
    )
    national_code = models.CharField(
        _("National Code"),
        blank=True,
        null=True,
        max_length=10,
        validators=[validate_national_code],
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(
        _("UserAccount Creation Date"), default=timezone.now
    )

    USERNAME_FIELD = "phone"

    objects = EcomUserManager()

    @property
    def full_name(self):
        if not self.first_name and not self.last_name:
            return None
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        "To distinguish user model from admin model by using this method"
        return False

    def __str__(self):
        return f"User: {self.username} , Phone number:{self.phone}"