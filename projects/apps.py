"""Конфиг приложения projects."""
from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """Регистрация приложения projects в Django."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "projects"
    verbose_name = "Проекты"
