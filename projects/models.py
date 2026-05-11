"""Модель проекта.

Используется ``TextChoices`` Django 3+, чтобы статусы были типобезопасными
и не требовали ручной поддержки ``STATUS_CHOICES``-кортежей и констант
с ``len(...)``.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse

from users.models import User


class Project(models.Model):
    """Pet-проект, к которому ищут участников."""

    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    name = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField(
        "Дата создания", auto_now_add=True,
    )
    github_url = models.URLField(
        "GitHub",
        blank=True,
        default="",
        validators=[User.github_validator],
    )
    status = models.CharField(
        "Статус",
        max_length=max(len(value) for value, _ in Status.choices),
        choices=Status.choices,
        default=Status.OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
        verbose_name="Участники",
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("projects:detail", args=[self.pk])

    @property
    def is_open(self) -> bool:
        return self.status == self.Status.OPEN
