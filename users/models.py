"""Кастомная модель пользователя.

Аутентификация по email вместо username. Реализована поверх
``AbstractBaseUser`` + ``PermissionsMixin``: используем минимум кода,
а не наследуемся от ``AbstractUser`` — чтобы не тащить ненужное поле
``username``.
"""
from __future__ import annotations

import io
import secrets
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from django.db import models
from PIL import Image, ImageDraw, ImageFont


# --- Хелперы ---------------------------------------------------------------

# Палитра-плашка для placeholder-аватара.
_PALETTE = (
    "#385F8E", "#7B5FA8", "#3F9A6F", "#C58145",
    "#B95C73", "#369494", "#677484", "#946595",
    "#4D7548", "#A8623F",
)


def _build_placeholder_image(letter: str, side: int = 256) -> ContentFile:
    """Рисует PNG с одной заглавной буквой на цветном фоне."""
    canvas = Image.new("RGB", (side, side), color=secrets.choice(_PALETTE))
    pen = ImageDraw.Draw(canvas)
    char = (letter or "?")[0].upper()
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=int(side * 0.55))
    except OSError:
        font = ImageFont.load_default()
    box = pen.textbbox((0, 0), char, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    pen.text(
        ((side - w) / 2 - box[0], (side - h) / 2 - box[1]),
        char,
        fill="white",
        font=font,
    )
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)
    return ContentFile(buf.getvalue())


# --- Manager ---------------------------------------------------------------


class UserManager(BaseUserManager):
    """Менеджер, работающий по email вместо username."""

    use_in_migrations = True

    def _construct(self, *, email: str, password: str, **extra):
        if not email:
            raise ValueError("Email обязателен")
        person = self.model(email=self.normalize_email(email), **extra)
        person.set_password(password)
        person.save(using=self._db)
        return person

    def create_user(self, email=None, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._construct(email=email, password=password, **extra)

    def create_superuser(self, email=None, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if not extra.get("is_staff"):
            raise ValueError("Superuser требует is_staff=True")
        if not extra.get("is_superuser"):
            raise ValueError("Superuser требует is_superuser=True")
        return self._construct(email=email, password=password, **extra)


# --- Сама модель -----------------------------------------------------------


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь платформы TeamFinder."""

    # Валидаторы — Django'овский RegexValidator + одна проверка ниже.
    phone_validator = RegexValidator(
        regex=r"^(\+7|8)\d{10}$",
        message="Телефон в формате 8XXXXXXXXXX или +7XXXXXXXXXX",
    )
    github_validator = RegexValidator(
        regex=r"^https?://(www\.)?github\.com/.+",
        message="Ссылка должна вести на github.com",
    )

    email = models.EmailField("Email", unique=True)
    name = models.CharField("Имя", max_length=124)
    surname = models.CharField("Фамилия", max_length=124)
    avatar = models.ImageField("Аватар", upload_to="avatars/")
    phone = models.CharField(
        "Телефон",
        max_length=12,
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
        "О себе", max_length=256, blank=True, default="",
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

    # --- Сервисные методы --------------------------------------------------

    def __str__(self) -> str:
        return f"{self.name} {self.surname} <{self.email}>"

    @staticmethod
    def canonical_phone(value: str | None) -> str | None:
        """Нормализует номер вида ``8XXXXXXXXXX`` к ``+7XXXXXXXXXX``."""
        if value and value.startswith("8") and len(value) == 11:
            return f"+7{value[1:]}"
        return value

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = self.canonical_phone(self.phone)
        if not self.avatar:
            self.avatar.save(
                f"{uuid.uuid4().hex}.png",
                _build_placeholder_image(self.name or self.email),
                save=False,
            )
        super().save(*args, **kwargs)
