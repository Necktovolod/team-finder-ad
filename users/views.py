"""Вьюхи приложения users."""
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from projects.services import paginate

from .constants import USERS_PER_PAGE
from .filters import apply_filter
from .forms import (
    AuthForm,
    PasswordUpdateForm,
    RegistrationForm,
    UpdateProfileForm,
)
from .models import User


def _redirect_logged_in(request):
    """Если уже залогинен — пинаем на список проектов."""
    if request.user.is_authenticated:
        return redirect("projects:list")
    return None


def register_page(request):
    """Регистрация нового пользователя."""
    redirect_response = _redirect_logged_in(request)
    if redirect_response:
        return redirect_response

    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("users:login")
    return render(request, "users/register.html", {"form": form})


def login_page(request):
    """Страница входа."""
    redirect_response = _redirect_logged_in(request)
    if redirect_response:
        return redirect_response

    form = AuthForm(request.POST or None, request=request)
    if form.is_valid():
        login(request, form.user)
        return redirect("projects:list")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    """Завершение сессии."""
    logout(request)
    return redirect("projects:list")


def participants_page(request):
    """Список всех пользователей с поддержкой фильтрации."""
    queryset = User.objects.all()
    chosen_filter = request.GET.get("filter") or ""

    if chosen_filter and request.user.is_authenticated:
        queryset = apply_filter(queryset, chosen_filter, request.user)

    page = paginate(queryset, request, page_size=USERS_PER_PAGE)
    context = {
        "participants": page.object_list,
        "page_obj": page,
        "active_filter": chosen_filter,
    }
    return render(request, "users/participants.html", context)


def profile_page(request, pk):
    """Публичный профиль пользователя."""
    target = get_object_or_404(User, pk=pk)
    return render(request, "users/user-details.html", {"user": target})


@login_required
def edit_profile_page(request):
    """Редактирование собственного профиля."""
    form = UpdateProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )
    if form.is_valid():
        form.save()
        return redirect("users:detail", request.user.id)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password_page(request):
    """Смена пароля авторизованным пользователем."""
    form = PasswordUpdateForm(request.user, request.POST or None)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect("users:detail", request.user.id)
    return render(request, "users/change_password.html", {"form": form})
