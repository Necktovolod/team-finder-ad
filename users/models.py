"""Модель пользователя."""
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .avatar import render_avatar
from .constants import (
    ABOUT_FIELD_LENGTH,
    EMAIL_FIELD_LENGTH,
    FIRST_NAME_LENGTH,
    LAST_NAME_LENGTH,
    PHONE_FIELD_LENGTH,
)
from .managers import UserManager
from .services import to_canonical_phone
from .validators import github_link_validator, phone_format_validator


class User(AbstractBaseUser, PermissionsMixin):
    """Кастомный пользователь, аутентифицируется по email."""

    email = models.EmailField(
        "Email", unique=True, max_length=EMAIL_FIELD_LENGTH,
    )
    name = models.CharField("Имя", max_length=FIRST_NAME_LENGTH)
    surname = models.CharField("Фамилия", max_length=LAST_NAME_LENGTH)
    avatar = models.ImageField("Аватар", upload_to="avatars/")
    phone = models.CharField(
        "Телефон",
        max_length=PHONE_FIELD_LENGTH,
        unique=True,
        blank=True,
        null=True,
        validators=[phone_format_validator],
    )
    github_url = models.URLField(
        "GitHub",
        blank=True,
        default="",
        validators=[github_link_validator],
    )
    about = models.TextField(
        "О себе", max_length=ABOUT_FIELD_LENGTH, blank=True, default="",
    )
    is_active = models.BooleanField("Активный", default=True)
    is_staff = models.BooleanField("Администратор", default=False)
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
            self.phone = to_canonical_phone(self.phone)
        if not self.avatar:
            self.avatar.save(
                f"{uuid.uuid4().hex}.png",
                render_avatar(self.name or self.email),
                save=False,
            )
        super().save(*args, **kwargs)
