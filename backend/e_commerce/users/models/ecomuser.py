from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone

from user.validators import (
    validate_phone,
    validate_username,
    validate_national_code,
    validate_postal_code,
)
from user.managers import EcomUserManager

# this model does not contain any superuser or admin, as theres a seperate model for that purpose.
class EcomUser(AbstractBaseUser):
    first_name = models.CharField(_("First Name"), max_length=50, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=50, blank=True)
    username = models.CharField(
        _("Username"),
        unique=True,
        help_text=_(
            "Maximum of 50 characters. Only letters, digits and the special character . are allowed"
        ),
        validators=[username_validator],
        error_messages={
            "null": _("The username cannot be null"),
            "blank": _("The username cannot be blank"),
            "unique": _("The username already exists"),
            "invalid": _(
                "The username is invalid. Please refer to username definition constraints."
            ),
        },
    )
    email = models.EmailField(_("Email Address"), blank=True)
    phone = models.CharField(
        _("Phone Number"), max_length=13, validators=[validate_phone]
    )
    national_code = models.CharField(
        _("National Code"),
        blank=True,
        max_length=10,
        validators=[validate_national_code],
    )
    postal_code = models.CharField(
        _("Postal Code"),
        blank=True,
        max_length=10,
        validators=[validate_postal_code],
    )
    address = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(
        _("UserAccount Creation Date"), default=timezone.now
    )

    USERNAME_FIELD = None

    objects = EcomUserManager()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"User: {self.username} , Phone number:{self.phone}"

