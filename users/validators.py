"""Валидаторы для модели User."""
import re

from django.core.exceptions import ValidationError

from .constants import GITHUB_URL_PATTERN, PHONE_PATTERN


def phone_format_validator(value: str) -> None:
    """Принимает только формат `8XXXXXXXXXX` или `+7XXXXXXXXXX`."""
    if not re.fullmatch(PHONE_PATTERN, value or ""):
        raise ValidationError(
            "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX",
        )


def github_link_validator(value: str) -> None:
    """Допускает только ссылки на github.com (либо пустую строку)."""
    if not value:
        return
    if not re.match(GITHUB_URL_PATTERN, value):
        raise ValidationError("Ссылка должна вести на github.com")
