import random
import string
from datetime import datetime
from typing import Union

from django.core.cache import cache

from .tasks import send_sms

VERIFY_PHONE_CACHE_BASE_KEY = "verify:"
SMS_COOLDOWN_CACHE_BASE_KEY = "cooldown:"
VERIFY_CACHE_DURATION = 60 * 15
COOLDOWN_CACHE_DURATION = 60 * 2


def current_time(time_format: str = "%H:%M:%S") -> str:
    "Returns the current time in provided format"
    return datetime.now().strftime(time_format)


def create_verification_msg(code: Union[str, int]) -> str:
    return f"کد فعالسازی: {code}\nسامانه پیچی کالا\nزمان ارسال {current_time()}"


def create_forgot_password_msg(code: Union[str, int]) -> str:
    return f"کد فراموشی رمز عبور: {code}\nسامانه پیچی کالا\nزمان ارسال {current_time()}"


def create_sms_cooldown_cache_key(phone: str) -> str:
    return SMS_COOLDOWN_CACHE_BASE_KEY + phone


def create_phone_verify_cache_key(phone: str) -> str:
    return VERIFY_PHONE_CACHE_BASE_KEY + phone


def generate_random_code(length: int = 6) -> str:
    return "".join(random.choice(string.digits) for _ in range(length))


def set_sms_cache_keys(phone_number: str, verification_code: str) -> None:
    """Set cache keys for phone verification and SMS cooldown."""
    cache.set(
        create_phone_verify_cache_key(phone_number),
        verification_code,
        VERIFY_CACHE_DURATION,
    )
    cache.set(
        create_sms_cooldown_cache_key(phone_number), True, COOLDOWN_CACHE_DURATION
    )


def process_phone_verification(phone_number: str) -> None:
    """
    Generates a verification code, set related cache keys and
    use celery task queue to send the SMS.
    """
    verification_code = generate_random_code()
    set_sms_cache_keys(phone_number, verification_code)
    send_sms.delay(
        reciever_phone_number=phone_number,
        message=create_verification_msg(verification_code),
    )
