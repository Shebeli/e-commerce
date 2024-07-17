from django_filters import rest_framework as filters
from product.models import Product


class ProductFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontain")
    subcategory = filters.CharFilter(
        field_name="subcategory__name", lookup_expr="iexact"
    )
    tags = filters.CharFilter(method="filter_by_tag_names")
    price_min = filters.NumberFilter(field_name="main_price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="main_price", lookup_expr="lte")
    in_stock = filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["in_stock", "subcategory", "price_min", "price_max", "name"]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.available()
        return queryset

    def filter_by_tag_names(self, queryset, name, value):
        tag_names = value.split(",")
        return queryset.filter(tags__name__in=tag_names).distinct()