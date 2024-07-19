import pytest

from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APIClient

from ecom_user.models import EcomUser
from ecom_user_profile.models import CustomerAddress
from product.models import Product

from .test_serializers import (
    sample_product_instance_factory,
    subcategory_obj,
    tag_objs,
    sample_category_instance_factory,
    sample_product_data_factory,
    sample_tags_instances_factory,
    full_product_data_factory,
    sample_technical_data,
    sample_variants_data,
)


# ---------------
#    Fixtures
# ---------------


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def customer_credentials():
    return {"phone": "09377964142", "password": "1234"}


@pytest.fixture
def seller_credentials():
    return {"phone": "09377964143", "password": "1234"}


@pytest.fixture
def customer_instance(db, customer_credentials):
    return EcomUser.objects.create_user(**customer_credentials)


@pytest.fixture
def seller_instance(db, seller_credentials):
    user = EcomUser.objects.create_user(**seller_credentials)
    user.seller_profile.is_verified = True
    user.save()
    return user


@pytest.fixture
def product_instance(sample_product_instance_factory, seller_instance):
    def create_product():
        product = sample_product_instance_factory()
        product.owner = seller_instance
        product.save()
        return product

    return create_product


@pytest.fixture
def api_client_with_customer_credentials(db, customer_instance):
    api_client = APIClient()
    api_client.force_authenticate(user=customer_instance)
    return api_client


@pytest.fixture
def api_client_with_seller_credentials(db, seller_instance):
    api_client = APIClient()
    api_client.force_authenticate(user=seller_instance)
    return api_client


# ---------------
#   Test Cases
# ---------------


@pytest.mark.django_db
def test_seller_can_create_product(
    api_client_with_seller_credentials, sample_product_data_factory
):
    url = reverse("product-list")
    product_data = sample_product_data_factory()
    response = api_client_with_seller_credentials.post(url, data=product_data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_seller_can_delete_owned_product(
    api_client_with_seller_credentials, product_instance
):
    product = product_instance()
    url = reverse("product-detail", args=[product.id])
    response = api_client_with_seller_credentials.delete(url, data={"id": product.id})
    assert response.status_code == 204


@pytest.mark.django_db
def test_seller_can_update_owned_product(
    api_client_with_seller_credentials, product_instance
):
    product = product_instance()
    url = reverse("product-detail", args=[product.id])
    response = api_client_with_seller_credentials.patch(url, data={"name": "new name"})
    assert response.status_code == 200
    assert response.data["name"] == "new name"


@pytest.mark.django_db
def test_product_view_count_increases_on_view(
    api_client_with_seller_credentials, product_instance
):
    client_ip = "127.0.0.1"  # default ip used by APIClient
    redis_client = cache.client.get_client()
    product = product_instance()
    url = reverse("product-detail", args=[product.id])
    response = api_client_with_seller_credentials.get(url)
    assert response.status_code == 200

    # check to see if the cache key has been created for tracking
    redis_key = f"product:{product.id}:ip:{client_ip}"
    assert redis_client.exists(redis_key) == 1

    # check to see if the view count has increased
    product = Product.objects.get(id=product.id)
    assert product.view_count == 1


@pytest.mark.django_db
def test_product_can_be_created(
    api_client_with_seller_credentials, tag_objs, subcategory_obj
):
    url = reverse("product-list")
    response = api_client_with_seller_credentials.post(
        url,
        data={
            "name": "chair",
            "main_price": 200,
            "subcategory": subcategory_obj.id,
            "tags": [tag.id for tag in tag_objs],
        },
    )
    assert response.status_code == 201
    assert Product.objects.get(id=response.data["id"])


@pytest.mark.django_db
def test_product_has_extra_details_for_owner():
    pass


@pytest.mark.django_db
def test_product_list_filter(api_client_with_customer_credentials):
    pass
