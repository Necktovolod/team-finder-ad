"""Модель проекта."""
from django.conf import settings
from django.db import models
from django.urls import reverse

from users.validators import github_link_validator

from .constants import (
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_STATUS_CHOICES,
    PROJECT_STATUS_MAX_LENGTH,
    PROJECT_STATUS_OPEN,
)


class Project(models.Model):
    """Pet-проект, на который пользователь ищет тиммейтов."""

    name = models.CharField(
        "Название", max_length=PROJECT_NAME_MAX_LENGTH,
    )
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
        "GitHub", blank=True, default="", validators=[github_link_validator],
    )
    status = models.CharField(
        "Статус",
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=PROJECT_STATUS_CHOICES,
        default=PROJECT_STATUS_OPEN,
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
        """Канонический URL для отображения проекта на сайте."""
        return reverse("projects:detail", args=[self.pk])
