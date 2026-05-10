"""Форма создания/редактирования проекта."""
from django import forms

from .constants import PROJECT_STATUS_CHOICES
from .models import Project


class ProjectForm(forms.ModelForm):
    """Форма для страниц «Создать» и «Редактировать» проект."""

    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на Github",
            "status": "Статус",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "status": forms.Select(choices=PROJECT_STATUS_CHOICES),
        }
