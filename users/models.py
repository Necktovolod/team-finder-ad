"""Кастомная модель пользователя.

Аутентификация по email вместо username. Реализована поверх
``AbstractBaseUser`` + ``PermissionsMixin``: используем минимум кода,
а не наследуемся от ``AbstractUser`` — чтобы не тащить ненужное поле
``username``.
"""
from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models

from .constants import (
    ABOUT_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    SURNAME_MAX_LENGTH,
)
from .managers import UserManager
from .service import build_placeholder_avatar


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь платформы TeamFinder."""

    phone_validator = RegexValidator(
        regex=r"^(\+7|8)\d{10}$",
        message="Телефон в формате 8XXXXXXXXXX или +7XXXXXXXXXX",
    )
    github_validator = RegexValidator(
        regex=r"^https?://(www\.)?github\.com/.+",
        message="Ссылка должна вести на github.com",
    )

    email = models.EmailField(
        "Email", unique=True, max_length=EMAIL_MAX_LENGTH,
    )
    name = models.CharField("Имя", max_length=NAME_MAX_LENGTH)
    surname = models.CharField("Фамилия", max_length=SURNAME_MAX_LENGTH)
    avatar = models.ImageField("Аватар", upload_to="avatars/")
    phone = models.CharField(
        "Телефон",
        max_length=PHONE_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        validators=[phone_validator],
    )
    github_url = models.URLField(
        "GitHub",
        blank=True,
        default="",
        validators=[github_validator],
    )
    about = models.TextField(
        "О себе", max_length=ABOUT_MAX_LENGTH, blank=True, default="",
    )
    is_active = models.BooleanField("Активный", default=True)
    is_staff = models.BooleanField("Сотрудник", default=False)
    favorites = models.ManyToManyField(
        "projects.Project",
        related_name="interested_users",
        blank=True,
        verbose_name="Избранные проекты",
    )
    date_joined = models.DateTimeField(
        "Дата регистрации", auto_now_add=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return f"{self.name} {self.surname} <{self.email}>"

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = self.canonical_phone(self.phone)
        if not self.avatar:
            self.avatar.save(
                f"{uuid.uuid4().hex}.png",
                build_placeholder_avatar(self.name or self.email),
                save=False,
            )
        super().save(*args, **kwargs)

    @staticmethod
    def canonical_phone(value: str | None) -> str | None:
        """Нормализует номер вида ``8XXXXXXXXXX`` к ``+7XXXXXXXXXX``."""
        if value and value.startswith("8") and len(value) == 11:
            return f"+7{value[1:]}"
        return value
