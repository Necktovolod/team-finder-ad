"""Админка для модели User."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)
from django.db.models import Count
from django.utils.html import format_html

from .constants import ADMIN_AVATAR_THUMB_PX
from .models import User


class _AdminSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "name", "surname")


class _AdminChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Регистрация модели User в админке Django."""

    add_form = _AdminSignupForm
    form = _AdminChangeForm
    change_password_form = AdminPasswordChangeForm
    model = User

    list_display = (
        "id",
        "avatar_tag",
        "email",
        "name",
        "surname",
        "participated_projects_count",
        "is_staff",
        "is_active",
    )
    list_display_links = ("id", "email")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "name", "surname")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Личные данные",
            {"fields": (
                "name", "surname", "avatar", "about", "phone", "github_url",
            )},
        ),
        (
            "Права",
            {"fields": (
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions",
            )},
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email", "name", "surname", "password1", "password2",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        """Аннотируем количество проектов одним SQL, чтобы избежать N+1."""
        return (
            super()
            .get_queryset(request)
            .annotate(_participated_count=Count("participated_projects"))
        )

    @admin.display(description="Аватар")
    def avatar_tag(self, obj: User) -> str:
        if not obj.avatar:
            return ""
        return format_html(
            '<img src="{}" width="{}" height="{}" '
            'style="border-radius:50%;object-fit:cover" />',
            obj.avatar.url,
            ADMIN_AVATAR_THUMB_PX,
            ADMIN_AVATAR_THUMB_PX,
        )

    @admin.display(
        description="Проектов",
        ordering="_participated_count",
    )
    def participated_projects_count(self, obj: User) -> int:
        return obj._participated_count
