import logging

import requests
from requests.exceptions import RequestException
from zibal.client import ZibalIPGClient
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
from celery import shared_task
from zibal.exceptions import RequestError, ResultError
from zibal.response_codes import STATUS_CODES

from product.models import ProductVariant
from order.models import Order
from financeops.models import Payment
from financeops.models import Transaction, IPG

logger = logging.getLogger("order")


@shared_task(bind=True, max_retries=5, default_retry_delay=45)
def handle_payment(self, track_id: int, payment_id: int) -> None:
    """
    After a `Payment` instance is created, this task should be
    executed after 20 minutes

    The payment status will be checked and the order or wallet status will
    be updated according to the response recieved from the IPG.
    """
    try:
        payment = Payment.objects.get(id=payment_id)
    except Order.DoesNotExist:
        logger.error(
            (
                f"Failed to resolve given payment object using order_id: {payment_id} "
                f"from the database in the following task: \n"
                f"task ID: {self.task.id} | task name: {self.request.task}"
            )
        )
        return

    # payment is paid most likely, so no need for inqurying
    if payment.status not in (Payment.UNPAID, Payment.PAYING):
        logger.info(
            (
                f"The order with id of {payment} is no longer in UNPAID or PAYING status"
                f"Order's current status: {payment.status}"
            )
        )
        return

    # order is still unpaid, inqurying to make sure that the purchase is completed.
    client = ZibalIPGClient(
        settings.ZIBAL_MERCHANT, raise_on_invalid_result=True, logger=logger
    )
    # zibal IPG status code meanings
    PAID_AND_VERIFIED = 1
    PAID_AND_UNVERIFIED = 2
    try:
        response_data = client.inquiry_transaction(track_id=track_id)
        if response_data.status == PAID_AND_UNVERIFIED:
            verify_data = client.verify_transaction(track_id)
            payment.paid_amount = verify_data.amount
            payment.status = Payment.PROCESSING
        elif response_data.status == PAID_AND_VERIFIED:
            payment.paid_amount = response_data.amount
            payment.status = Order.PAID
        else:
            payment.status = Order.UNPAID
        payment.save()
    except RequestError as exc:
        raise self.retry(exc=exc)
    except ResultError as exc:
        logger.error(
            f"Unexpected response received from the IPG webserver: {exc}"
            f"order_id: {payment_id} | "
            f"task id: {self.task.id} | task name: {self.request.task}"
        )
    except Order.DoesNotExist:
        logger.error(
            (
                f"Failed to resolve given payment object using the following payment id: {payment_id} "
                f"from the database in the following task: \n"
                f"task ID: {self.task.id} | task name: {self.request.task}"
            )
        )


@shared_task(bind=True, max_retries=5, default_retry_delay=75)
def cancel_unpaid_order(self, order_id):
    """
    For cancelling orders which haven't been paid for about 1-2 hours,
    which will also release the reserved stocks occupied by the order.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(
            (
                f"Failed to resolve given order object using order_id: {order_id} "
                f"from the database in the following task: \n"
                f"task ID: {self.task.id} | task name: {self.request.task}"
            )
        )
        return
    if order.status == Order.PAYING:
        raise self.retry(countdown=60 * 20)
    if order.status == Order.UNPAID:
        product_variants = []
        for order_item in order.items.all():
            product_variant = order_item.product_variant
            product_variant.reserved_stock -= order_item.quantity
            product_variant.on_hand_stock += order_item.quantity
            product_variants.append(product_variant)
        order.status = Order.CANCELLED
        order.cancelled_by = order.SERVER
        with transaction.atomic():
            ProductVariant.objects.bulk_update(
                product_variants, ["reserved_stock", "on_hand_stock"]
            )
            order.save()


@shared_task(bind=True)
def update_order_to_delivered(self, order_id: int):
    """
    After a period of 5 business days of shipment, if no complaints have been
    recieved from the customer, the order's status is updated to DELIVERED.

    However, if the order is not delivered and the customer
    informs the server that the order hasn't been delivered,
    customer support should intervene and check what has happened
    with the order, and should follow up with approprite actions
    inorder to resolve the issue.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(
            (
                f"Failed to resolve given order object using order_id: {order_id} "
                f"from the database in the following task: \n"
                f"task ID: {self.task.id} | task name: {self.request.task}"
            )
        )
        return
    commission_rate = settings.COMMISSION_RATE
    seller_wallet = order.seller.wallet
    with transaction.atomic():
        Transaction.objects.create(
            type=Transaction.ORDER_REVENUE,
            commission_rate=commission_rate,
            order=order,
            amount=order.total_price * commission_rate,
        )
        seller_wallet += order.total_price * commission_rate
        seller_wallet.save()
        order.status = Order.DELIVERED
        order.save()


@shared_task
def check_and_cache_ipg_status():
    """
    Cache the available ipgs with a get request to assert whether the IPG
    service is running or not.
    """
    IPGs = IPG.objects.all()
    if not IPGs:
        logger.critical(
            "One IPG instance should at least exist for IPG status scheduler checker."
        )
        return
    available_ipgs = []
    for ipg in IPG.objects.all():
        try:
            response = requests.get(ipg.status_check_url, timeout=5)
            if response.status_code != 200:
                logger.warning(
                    f"Unexpected response status code on service check: {response.status_code} content: {response.content}"
                    f"\n IPG service {ipg.service_name} is unavailable, disabling gateway."
                )
                return

        except RequestException as err:
            logger.warning(
                f"A network request error has occured on IPG status check: {err}"
                f"\n IPG service {ipg.service_name} is unavailable, disabling gateway."
            )
            return
        available_ipgs.append(ipg.id)
    cache.set("available_ipgs", available_ipgs)
