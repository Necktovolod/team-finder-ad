"""Админка для модели Project."""
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Регистрация Project в админке."""

    list_display = (
        "id", "name", "owner", "status", "participants_inline", "created_at",
    )
    list_display_links = ("id", "name")
    list_filter = ("status",)
    search_fields = ("name", "description", "owner__email")
    autocomplete_fields = ("owner", "participants")
    readonly_fields = ("created_at",)
    fields = (
        "name", "description", "owner", "github_url",
        "status", "participants", "created_at",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("owner")
            .prefetch_related("participants")
        )

    @admin.display(description="Участники")
    def participants_inline(self, obj: Project) -> str:
        return ", ".join(p.email for p in obj.participants.all())
