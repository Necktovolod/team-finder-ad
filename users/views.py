"""Class-based вьюхи приложения users.

Где можно — переиспользуем готовые Django-вьюхи из
``django.contrib.auth.views``. Кастомные вьюхи (регистрация,
список юзеров с фильтрацией, редактирование профиля)
оформлены в одном стиле с :mod:`projects.views`.
"""
from __future__ import annotations

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
)
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import LoginForm, ProfileEditForm, SignupForm
from .models import User


# ---------- Auth -----------------------------------------------------------


class SignupView(CreateView):
    """Регистрация нового пользователя."""

    form_class = SignupForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("projects:list")
        return super().dispatch(request, *args, **kwargs)


class TeamFinderLoginView(LoginView):
    """Вход в систему: использует встроенный Django-вью."""

    template_name = "users/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Наша LoginForm принимает request как именованный аргумент.
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        login(self.request, form.user_cache)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("projects:list")


class TeamFinderLogoutView(LogoutView):
    """Выход с редиректом на список проектов."""

    next_page = reverse_lazy("projects:list")

    # Django >= 5 запрещает logout по GET — а шаблоны Практикума его шлют.
    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class TeamFinderPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Смена пароля авторизованным пользователем."""

    template_name = "users/change_password.html"

    def get_success_url(self):
        return reverse("users:detail", args=[self.request.user.id])


# ---------- Профиль --------------------------------------------------------


class UserDetailView(DetailView):
    """Публичный профиль пользователя."""

    model = User
    template_name = "users/user-details.html"
    context_object_name = "user"


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Редактирование собственного профиля."""

    form_class = ProfileEditForm
    template_name = "users/edit_profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("users:detail", args=[self.request.user.id])


# ---------- Список пользователей с фильтрами -------------------------------


# Маппинг ``?filter=...`` → выражения для ``QuerySet.filter``.
# Используется внутри ``UserListView.get_queryset``.
FILTER_LOOKUPS = {
    "owners-of-favorite-projects": lambda u: {
        "owned_projects__in": u.favorites.all(),
    },
    "owners-of-participating-projects": lambda u: {
        "owned_projects__in": u.participated_projects.all(),
    },
    "interested-in-my-projects": lambda u: {
        "favorites__in": u.owned_projects.all(),
    },
    "participants-of-my-projects": lambda u: {
        "participated_projects__in": u.owned_projects.all(),
    },
}


class UserListView(ListView):
    """Список всех пользователей платформы.

    Фильтрация через GET-параметр ``filter=<key>``.
    """

    model = User
    paginate_by = 12
    template_name = "users/participants.html"
    context_object_name = "participants"

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        chosen = self.request.GET.get("filter") or ""
        if chosen and self.request.user.is_authenticated:
            lookup_factory = FILTER_LOOKUPS.get(chosen)
            if lookup_factory is not None:
                qs = qs.filter(**lookup_factory(self.request.user)).distinct()
                if chosen == "participants-of-my-projects":
                    qs = qs.exclude(pk=self.request.user.pk)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_filter"] = self.request.GET.get("filter") or ""
        return ctx
