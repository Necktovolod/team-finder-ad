"""Class-based вьюхи для приложения projects.

Списки выводятся через ``ListView`` (`paginate_by = 12`),
страница проекта — через ``DetailView`` с предзагрузкой связанных
данных. AJAX-эндпоинты — короткие наследники ``View``, чтобы
переиспользовать механизмы ``LoginRequiredMixin`` / ``UserPassesTestMixin``.
"""
from __future__ import annotations

from http import HTTPStatus

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormMixin
from django.utils.decorators import method_decorator

from .forms import ProjectForm
from .models import Project


# ---------- List views ----------


class _ProjectListBase(ListView):
    """Базовый ListView, подгружающий ``owner`` и ``participants``."""

    model = Project
    paginate_by = 12
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
        return super().get_queryset().filter(interested_users=self.request.user)


# ---------- Detail / Create / Edit ----------


class ProjectDetailView(DetailView):
    """Детальная страница проекта."""

    model = Project
    context_object_name = "project"
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

    def get_success_url(self):
        return self.object.get_absolute_url()


class _OwnerOrStaffMixin(UserPassesTestMixin):
    """Разрешает доступ только владельцу проекта или администратору."""

    def test_func(self):
        project = self.get_object()
        return (
            project.owner_id == self.request.user.id
            or self.request.user.is_staff
        )

    def handle_no_permission(self):
        # Без алёрта 403 — просто откатываем на страницу проекта.
        return _redirect_to(self.get_object())


def _redirect_to(project: Project):
    from django.shortcuts import redirect
    return redirect(project.get_absolute_url())


class ProjectUpdateView(LoginRequiredMixin, _OwnerOrStaffMixin, UpdateView):
    """Редактирование проекта владельцем или администратором."""

    model = Project
    form_class = ProjectForm
    template_name = "projects/create-project.html"
    extra_context = {"is_edit": True}

    def get_success_url(self):
        return self.object.get_absolute_url()


# ---------- AJAX endpoints (всё ещё CBV, но коротенькие) ----------


class _JsonAjaxView(LoginRequiredMixin, FormMixin, DetailView):
    """База для AJAX-вьюх: только POST, отдаёт JsonResponse."""

    model = Project

    @method_decorator(require_POST)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):  # noqa: D401
        # Защита: GET не нужен; на всякий случай блокируем (require_POST уже это делает).
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


# ---------- URL-обёртки ----------

# Пара публичных reverse_lazy-имён, используемых в settings.LOGIN_URL и redirect'ах.
LOGIN_URL = reverse_lazy("users:login")
