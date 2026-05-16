"""Class-based вьюхи для приложения projects.

Списки выводятся через :class:`ListView` (``paginate_by`` из constants),
страница проекта — через :class:`DetailView` с предзагрузкой связанных
данных. AJAX-эндпоинты — короткие наследники :class:`View`, чтобы
переиспользовать механизмы ``LoginRequiredMixin``.
"""
from __future__ import annotations

from http import HTTPStatus

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormMixin

from .constants import PROJECTS_PER_PAGE
from .forms import ProjectForm
from .mixins import OwnerOrStaffMixin
from .models import Project


# ---------- Корневой redirect, подключён в team_finder/urls.py ------------


def home_redirect(request):
    """Главная страница перенаправляет на список проектов."""
    return redirect("projects:list")


# ---------- List views ----------


class _ProjectListBase(ListView):
    """Базовый ListView, подгружающий ``owner`` и ``participants``."""

    model = Project
    paginate_by = PROJECTS_PER_PAGE
    context_object_name = "projects"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("owner")
            .prefetch_related("participants")
            .order_by("-created_at")
        )


class ProjectListView(_ProjectListBase):
    """Главная страница: лента всех проектов."""

    template_name = "projects/project_list.html"


class FavoriteProjectsView(LoginRequiredMixin, _ProjectListBase):
    """Страница «Избранное» — только проекты, добавленные текущим юзером."""

    template_name = "projects/favorite_projects.html"

    def get_queryset(self):
        return super().get_queryset().filter(
            interested_users=self.request.user,
        )


# ---------- Detail / Create / Edit ----------


class ProjectDetailView(DetailView):
    """Детальная страница проекта."""

    model = Project
    template_name = "projects/project-details.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("owner")
            .prefetch_related("participants")
        )


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Создание нового проекта."""

    form_class = ProjectForm
    template_name = "projects/create-project.html"
    extra_context = {"is_edit": False}

    def form_valid(self, form):
        project = form.save(commit=False)
        project.owner = self.request.user
        project.save()
        project.participants.add(self.request.user)
        self.object = project
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, OwnerOrStaffMixin, UpdateView):
    """Редактирование проекта владельцем или администратором.

    ``get_success_url`` определять не нужно — Django сам вызывает
    ``self.object.get_absolute_url()``.
    """

    model = Project
    form_class = ProjectForm
    template_name = "projects/create-project.html"
    extra_context = {"is_edit": True}


# ---------- AJAX endpoints ----------


class _JsonAjaxView(LoginRequiredMixin, FormMixin, DetailView):
    """База для AJAX-вьюх: только POST, отдаёт JsonResponse."""

    model = Project

    @method_decorator(require_POST)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # require_POST уже отсекает GET; этот метод — страховка
        # на случай если decorator снимут.
        return JsonResponse({}, status=HTTPStatus.METHOD_NOT_ALLOWED)


class ProjectCompleteView(_JsonAjaxView):
    """Закрытие проекта владельцем."""

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        if project.owner_id != request.user.id:
            return JsonResponse(
                {"status": "forbidden"}, status=HTTPStatus.FORBIDDEN,
            )
        if not project.is_open:
            return JsonResponse(
                {"status": "error", "project_status": project.status},
                status=HTTPStatus.BAD_REQUEST,
            )
        project.status = Project.Status.CLOSED
        project.save(update_fields=["status"])
        return JsonResponse(
            {"status": "ok", "project_status": project.status},
        )


class ToggleParticipateView(_JsonAjaxView):
    """Подключение / отключение пользователя как участника."""

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        link = project.participants
        if link.filter(pk=request.user.pk).exists():
            link.remove(request.user)
            return JsonResponse({"status": "ok", "participant": False})
        link.add(request.user)
        return JsonResponse({"status": "ok", "participant": True})


class ToggleFavoriteView(_JsonAjaxView):
    """Добавление / удаление проекта из избранного."""

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        favorites = request.user.favorites
        if favorites.filter(pk=project.pk).exists():
            favorites.remove(project)
            return JsonResponse({"status": "ok", "favorited": False})
        favorites.add(project)
        return JsonResponse({"status": "ok", "favorited": True})
