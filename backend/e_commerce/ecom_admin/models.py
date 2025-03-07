from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from ecom_core.validators import validate_username

from .managers import EcomAdminManager


class EcomAdmin(AbstractBaseUser):
    ORDERMANAGER = "OM"
    INVENTORYMANAGER = "IM"
    SUPERVISOR = "SV"
    MANAGER = "MG"
    SUPERADMIN = "SA"
    ADMIN_ROLE_CHOICES = [
        (ORDERMANAGER, "Order Manager"),
        (INVENTORYMANAGER, "Inventory Manager"),
        (SUPERVISOR, "Super visor"),
        (MANAGER, "Manager"),
        (SUPERADMIN, "Super admin"),
    ]
    role = models.CharField(max_length=2, choices=ADMIN_ROLE_CHOICES)
    first_name = models.CharField(_("First Name"), max_length=50, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=50, blank=True)
    email = models.EmailField(_("Email Address"), unique=True)
    username = models.CharField(
        _("Username"),
        unique=True,
        help_text=_(
            "Maximum of 100 characters. Only letters, digits and the special character . are allowed"
        ),
        validators=[validate_username],
        error_messages={
            "null": _("The username cannot be null"),
            "blank": _("The username cannot be blank"),
            "unique": _("The username already exists"),
            "invalid": _(
                "The username is invalid. Please refer to username definition constraints."
            ),
        },
        max_length=100,
    )

    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(
        _("AdminAccount Creation Date"), default=timezone.now
    )

    objects = EcomAdminManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    @property
    def get_role(self):
        return self.role

    @property
    def is_admin(self):
        "To distinguish user model from admin model"
        return True

    @property
    def is_staff(self):
        return True

    @property
    def is_superuser(self):
        return self.role == self.SUPERADMIN

    def has_perm(self, perm, obj=None):
        if self.role == self.SUPERADMIN:
            return True
        # other roles perm should be implemented based on their role on what actions they can
        # commit.
        return False

    def has_module_perms(self, app_label):
        return self.is_superuser

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"Admin {self.username} with role {self.role}"
