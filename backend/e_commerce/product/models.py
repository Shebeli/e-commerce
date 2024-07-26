from django.db import models
from django.core import exceptions
from django.db.models import F, Sum, When, Value, Case
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ecom_core.validators import validate_rating
from ecom_user.models import EcomUser
from .managers import ProductManager


# Overall visualization of different category models is shown in the following tree:
# - MainCategory 1
#   - Category 1
#       - SubCategory 1
#       - SubCategory 2
#       - ...
#       - SubCategory p
#   - ...
#   - Category m
# - ...
# - MainCategory n
# ----------------------
# An Example:
# - Books and Stationery
#   - Books and Magazines
#       - Printed books
#       - Foreign and domestic magazines
# ....


class MainCategory(models.Model):
    name = models.CharField(max_length=30, unique=True)


class Category(models.Model):
    name = models.CharField(max_length=30, unique=True)
    main_category = models.ForeignKey(
        MainCategory, on_delete=models.CASCADE, related_name="categories"
    )


class SubCategory(models.Model):
    name = models.CharField(max_length=30, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="subcategories"
    )


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True, db_index=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """
    The main_variant field is the representative of the product, so fields such as price,
    image and ... are derived from the main variant instance when displaying the product
    information on a generic level.
    Also note that at least one product variant should be created for a Product,
    otherwise the product would not be valid to work with.
    """

    owner = models.ForeignKey(
        EcomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="owner",
        blank=False,
        db_index=True,
    )
    main_variant = models.OneToOneField(
        "ProductVariant",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="main_variant_of",
        db_index=True,
    )
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=500)
    subcategory = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    tags = models.ManyToManyField(Tag, related_name="products")
    rating = models.DecimalField(
        default=0.0, max_digits=1, decimal_places=1, validators=[validate_rating]
    )
    view_count = models.PositiveIntegerField(default=0, db_index=True)
    is_valid = models.GeneratedField(
        expression=Case(
            When(main_variant__isnull=False, then=Value(True)),
            default=Value(False),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        db_index=True,
    )

    objects = ProductManager()

    def increase_view_count(self) -> None:
        self.view_count = F("view_count") + 1  # to avoid race condition
        self.save(update_fields=["view_count"])
        self.refresh_from_db(fields=["view_count"])

    def get_on_hand_stock(self, use_db: bool = True):
        if use_db:
            return self.variants.aggregate(on_hand_stock=Sum(F("on_hand_stock")))[
                "on_hand_stock"
            ]
        return sum([variant.on_hand_stock for variant in self.variants.all()])

    def get_reserved_stock(self, use_db: bool = True):
        if use_db:
            return self.variants.aggregate(reserved_stock=Sum(F("reserved_stock")))[
                "reserved_stock"
            ]
        return sum([variant.reserved_stock for variant in self.variants.all()])

    def get_available_stock(self, use_db: bool = True):
        if use_db:
            return self.variants.aggregate(available_stock=Sum(F("available_stock")))[
                "available_stock"
            ]
        return sum([variant.available_stock for variant in self.variants.all()])

    def get_number_sold(self, use_db: bool = True):
        if use_db:
            return self.variants.aggregate(number_sold=Sum(F("numbers_sold")))[
                "number_sold"
            ]
        return sum([variant.number_sold for variant in self.variants.all()])

    @property
    def tag_names(self):
        return [tag.name for tag in self.tags.all()]

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class ProductVariant(models.Model):
    """
    At least one ProductVariant instance should exist for every Product,
    even for products with no variants (i.e. products with single variant or no
    variants both have one ProductVariant instance)
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants", db_index=True
    )
    name = models.CharField(max_length=50)
    price = models.PositiveIntegerField()
    image = models.ImageField(null=True, blank=True)
    on_hand_stock = models.PositiveIntegerField()
    reserved_stock = models.PositiveIntegerField(default=0)
    available_stock = models.GeneratedField(
        expression=F("on_hand_stock") - F("reserved_stock"),
        output_field=models.PositiveIntegerField(),
        db_persist=True,
        db_index=True,
    )
    numbers_sold = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.reserved_stock > self.on_hand_stock:
            raise exceptions.ValidationError(
                "Reserved stock cannot be larger than on-hand inventory"
            )
        return super().save(*args, **kwargs)

    @property
    def is_available(self):
        return self.available_stock > 0

    @property
    def owner(self):
        return self.product.owner


class ProductVariantImage(models.Model):
    product_variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField()


class TechnicalDetail(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="technical_details"
    )
    attribute = models.CharField(max_length=30)
    value = models.CharField(
        max_length=80, verbose_name="technical attribute description"
    )

    class Meta:
        unique_together = ("product", "attribute")

    @property
    def owner(self):
        return self.product.owner
