from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework import status
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from django.core import cache
from django_filters import rest_framework as filters
from ipware import get_client_ip

from product.models import Product, SubCategory, Tag
from product.serializers import (
    ProductSerializer,
    ProductListSerializer,
    CategorySerializer,
    TagSerializer,
    TechnicalDetailSerializer,
)
from product.permissions import IsAdminOrReadOnly
from product.filters import ProductFilter
from ecom_core.permissions import IsOwner


class ProductList(ListAPIView):
    "Note that providing a subcategory is required"

    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    filter_backends = [OrderingFilter, filters.DjangoFilterBackend]
    filterset_class = ProductFilter
    ordering_fields = ["main_price", "rating", "created_at", "view_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        subcategory = self.request.query_params.get("subcategory")
        if not subcategory:
            raise ParseError("Query parameter 'subcategory' should be provided")
        return super().get_queryset()


class ProductViewSet(ModelViewSet):
    """
    Admins/product owners can modify or delete existing products and create new products.
    Non-admin users can only retrieve the information of a product.
    """

    permission_classes = [IsAdminOrReadOnly | IsOwner]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [OrderingFilter, filters.DjangoFilterBackend]
    filterset_class = ProductFilter
    ordering_fields = ["main_price", "rating", "created_at", "view_count"]
    ordering = ["-created_at"]

    def retrieve(self, request, *args, **kwargs):
        """
        Increase the view count of a product by indentifying client's IP,
        with the cooldown of one day.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        user_ip, _ = get_client_ip(self.request)
        if not user_ip:
            return Response(serializer.data)
        redis_key = f"product:{instance.id}:ip:{user_ip}"
        redis_client = cache.client.get_client()
        if not redis_client.exists(redis_key):
            instance.increase_view_count()
            cooldown_period = 3600 * 24 # one hour in seconds * number of hours
            redis_client.setex(redis_key, cooldown_period, 1)  # a dummy value
        return Response(serializer.data)

    def get_object(self):

        product_obj = super().get_object()
        user_ip, is_routable = get_client_ip(self.request)
        if not user_ip:
            return product_obj
        redis_key = f"product:{product_obj.id}:ip:{user_ip}"
        redis_client = cache.client.get_client()
        if not redis_client.exists(redis_key):
            product_obj.increase_view_count()
            cooldown_period = 60 * 60 * 24
            redis_client.setex(redis_key, cooldown_period, 1)  # a dummy value
        return product_obj


class TagProductsViewSet(GenericViewSet, ListModelMixin):
    "For listing all products belonging to a certain tag or list of tags"
    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer

    def get_tag_names_or_400(self):
        tag_names = self.request.query_params.getlist("tag")
        if not tag_names:
            raise ParseError("Query parameter 'tag' should be provided")
        return tag_names

    def get_queryset(self):
        tag_names = self.get_tag_names_or_400()
        products = self.queryset.filter(tags__name__in=tag_names)
        if not products:
            raise NotFound("No products were found with the given tag name(s)")
        return products


class CategoryViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TagViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ProductsTechnicalDetailViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all()
    serializer_class = TechnicalDetailSerializer
