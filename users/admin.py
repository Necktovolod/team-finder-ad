"""Регистрация модели User в админке."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)
from django.utils.html import format_html

from .constants import ADMIN_AVATAR_PIXELS
from .models import User


class UserSignupForm(UserCreationForm):
    """Форма создания пользователя в админке."""

    class Meta:
        model = User
        fields = ("email", "name", "surname")


class UserUpdateForm(UserChangeForm):
    """Форма редактирования пользователя в админке."""

    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Настроенная админка для кастомного User."""

    add_form = UserSignupForm
    form = UserUpdateForm
    change_password_form = AdminPasswordChangeForm
    model = User

    list_display = (
        "id",
        "avatar_preview",
        "email",
        "name",
        "surname",
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
            {
                "fields": (
                    "name",
                    "surname",
                    "avatar",
                    "about",
                    "phone",
                    "github_url",
                ),
            },
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "surname",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    @admin.display(description="Аватар")
    def avatar_preview(self, obj: User) -> str:
        """Миниатюра аватара в списке пользователей."""
        if not obj.avatar:
            return ""
        return format_html(
            '<img src="{}" width="{}" height="{}" '
            'style="border-radius:50%;object-fit:cover" />',
            obj.avatar.url,
            ADMIN_AVATAR_PIXELS,
            ADMIN_AVATAR_PIXELS,
        )
