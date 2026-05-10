"""Конфиг приложения users."""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Регистрация приложения users в Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Пользователи"
