"""Вьюхи приложения projects."""
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .constants import PROJECT_STATUS_CLOSED, PROJECT_STATUS_OPEN
from .forms import ProjectForm
from .models import Project
from .services import base_project_queryset, paginate, with_related


# ---------------------------------------------------------------------------
#  Список и просмотр проектов
# ---------------------------------------------------------------------------


def project_list(request):
    """Главная страница: лента всех проектов."""
    queryset = base_project_queryset().order_by("-created_at")
    page = paginate(queryset, request)
    return render(
        request,
        "projects/project_list.html",
        {"projects": page.object_list, "page_obj": page},
    )


@login_required
def favorite_projects(request):
    """Страница «Избранное» — только владельцу."""
    queryset = with_related(request.user.favorites.all()).order_by(
        "-created_at",
    )
    page = paginate(queryset, request)
    return render(
        request,
        "projects/favorite_projects.html",
        {"projects": page.object_list, "page_obj": page},
    )


def project_detail(request, pk):
    """Детальная страница проекта."""
    project = get_object_or_404(base_project_queryset(), pk=pk)
    return render(
        request,
        "projects/project-details.html",
        {"project": project},
    )


# ---------------------------------------------------------------------------
#  Создание и редактирование проекта
# ---------------------------------------------------------------------------


@login_required
def create_project(request):
    """Страница создания нового проекта."""
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect("projects:detail", project.pk)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required
def edit_project(request, pk):
    """Редактирование проекта (доступно владельцу или админу)."""
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id != request.user.id and not request.user.is_staff:
        return redirect("projects:detail", project.pk)
    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid():
        form.save()
        return redirect("projects:detail", project.pk)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


# ---------------------------------------------------------------------------
#  AJAX-эндпоинты
# ---------------------------------------------------------------------------


@login_required
@require_POST
def complete_project(request, pk):
    """Закрыть проект — доступно только владельцу."""
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id != request.user.id:
        return JsonResponse(
            {"status": "forbidden"}, status=HTTPStatus.FORBIDDEN,
        )
    if project.status != PROJECT_STATUS_OPEN:
        return JsonResponse(
            {"status": "error", "project_status": project.status},
            status=HTTPStatus.BAD_REQUEST,
        )
    project.status = PROJECT_STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse(
        {"status": "ok", "project_status": PROJECT_STATUS_CLOSED},
    )


@login_required
@require_POST
def toggle_participate(request, pk):
    """Подключить/отключить пользователя как участника проекта."""
    project = get_object_or_404(Project, pk=pk)
    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        return JsonResponse({"status": "ok", "participant": False})
    project.participants.add(request.user)
    return JsonResponse({"status": "ok", "participant": True})


@login_required
@require_POST
def toggle_favorite(request, pk):
    """Добавить/убрать проект из избранного у текущего пользователя."""
    project = get_object_or_404(Project, pk=pk)
    if request.user.favorites.filter(pk=project.pk).exists():
        request.user.favorites.remove(project)
        return JsonResponse({"status": "ok", "favorited": False})
    request.user.favorites.add(project)
    return JsonResponse({"status": "ok", "favorited": True})
