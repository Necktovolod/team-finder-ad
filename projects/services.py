"""Вспомогательные функции для работы с проектами и пагинацией."""
from django.core.paginator import Page, Paginator
from django.db.models import QuerySet

from .constants import PROJECTS_PER_PAGE
from .models import Project


def with_related(queryset: QuerySet) -> QuerySet:
    """Подтягивает автора и список участников одним SQL-запросом.

    Используется во всех страницах со списком проектов и в детали
    проекта, чтобы избежать N+1 при рендере карточек.
    """
    return queryset.select_related("owner").prefetch_related("participants")


def base_project_queryset() -> QuerySet:
    """Базовый queryset с подгруженными связями для всех страниц."""
    return with_related(Project.objects.all())


def paginate(
    queryset: QuerySet, request, page_size: int = PROJECTS_PER_PAGE,
) -> Page:
    """Возвращает страницу пагинации для GET-параметра ``page``."""
    paginator = Paginator(queryset, page_size)
    return paginator.get_page(request.GET.get("page"))
