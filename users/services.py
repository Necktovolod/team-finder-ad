"""Чистые вспомогательные функции приложения users."""


def to_canonical_phone(value: str) -> str:
    """Приводит локальный российский номер `8XXXXXXXXXX` к `+7XXXXXXXXXX`."""
    if value and value.startswith("8") and len(value) == 11:
        return f"+7{value[1:]}"
    return value
