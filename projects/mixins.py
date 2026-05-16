"""Переиспользуемые миксины для CBV приложения projects."""
from __future__ import annotations

from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class OwnerOrStaffMixin(UserPassesTestMixin):
    """Разрешает доступ только владельцу объекта или администратору.

    Объект достаётся через :meth:`get_object` — миксин предполагает,
    что наследник умеет его возвращать (наследник от ``DetailView``,
    ``UpdateView``, ``DeleteView`` и т. п.) и что у объекта есть
    атрибут ``owner_id`` и метод ``get_absolute_url``.
    """

    def test_func(self) -> bool:
        obj = self.get_object()
        return (
            obj.owner_id == self.request.user.id
            or self.request.user.is_staff
        )

    def handle_no_permission(self):
        # Вместо 403-страницы мягко отправляем туда же, где объект.
        return redirect(self.get_object().get_absolute_url())
