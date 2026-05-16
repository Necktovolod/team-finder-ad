"""Менеджер для модели :class:`users.models.User`."""
from __future__ import annotations

from django.contrib.auth.models import BaseUserManager


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
