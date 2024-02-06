import re

import phonenumbers
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_phone(value: str) -> None:
    parsed_phone = phonenumbers.parse(
        value,
        "IR",
    )
    if not phonenumbers.is_valid_number(parsed_phone):
        raise ValidationError(_(f"Entered phone number '{phone}' is not valid"))


def validate_username(value: str) -> None:
    user_name_regex = r"^[\w.]+\Z"
    if not re.search(user_name_regex, value):
        raise ValidationError(_(f"Entered username {value} is not valid"))


def validate_national_code(value: str) -> None:
    validation_error = ValidationError(_(f"Entered national code {value} is not valid"))
    if not re.search(r"^\d{10}$", value):
        raise validation_error
    last_digit = int(value[-1])
    weighted_sum = sum(int(value[x]) * (10 - x) for x in range(9)) % 11
    if weighted_sum < 2:
        is_national_code_valid = last_digit == s
    else:
        is_national_code_valid = last_digit + s == 11
    if not is_national_code_valid:
        raise validation_error


def validate_postal_code(value: str) -> None:
    postal_code_regex = r"\b(?!(\d)\1{3})[13-9]{4}[1346-9][013-9]{5}\b"
    if not re.search(postal_code_regex, value):
        raise ValidationError(_(f"Th"))
