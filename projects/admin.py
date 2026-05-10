"""Регистрация модели Project в админке."""
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Удобный список и форма редактирования проектов в админке."""

    list_display = (
        "id",
        "name",
        "owner",
        "status",
        "members_summary",
        "created_at",
    )
    list_display_links = ("id", "name")
    list_filter = ("status",)
    search_fields = ("name", "description", "owner__email")
    autocomplete_fields = ("owner", "participants")
    readonly_fields = ("created_at",)
    fields = (
        "name",
        "description",
        "owner",
        "github_url",
        "status",
        "participants",
        "created_at",
    )

    def get_queryset(self, request):
        """Подгружаем связанные данные одним SQL-запросом."""
        return (
            super()
            .get_queryset(request)
            .select_related("owner")
            .prefetch_related("participants")
        )

    @admin.display(description="Участники")
    def members_summary(self, project: Project) -> str:
        """Список email участников в строку."""
        return ", ".join(
            participant.email for participant in project.participants.all()
        )
