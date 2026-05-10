"""Стратегии фильтрации списка пользователей.

Каждый фильтр — отдельный класс с двумя атрибутами:
* ``key`` — строка из GET-параметра ``?filter=...``;
* ``apply(queryset, current_user)`` — преобразование queryset.

Чтобы добавить новый фильтр, достаточно создать наследника
:class:`UserListFilter` и зарегистрировать в :data:`FILTERS_REGISTRY`.
"""
from django.db.models import QuerySet


class UserListFilter:
    """Базовый интерфейс для фильтров списка пользователей."""

    key: str = ""

    def apply(self, queryset: QuerySet, current_user) -> QuerySet:
        raise NotImplementedError


class FavoriteOwnersFilter(UserListFilter):
    """Авторы проектов, которые залогиненный добавил в избранное."""

    key = "owners-of-favorite-projects"

    def apply(self, queryset, current_user):
        return queryset.filter(
            owned_projects__in=current_user.favorites.all(),
        ).distinct()


class JoinedProjectOwnersFilter(UserListFilter):
    """Авторы проектов, в которых текущий пользователь — участник."""

    key = "owners-of-participating-projects"

    def apply(self, queryset, current_user):
        return queryset.filter(
            owned_projects__in=current_user.participated_projects.all(),
        ).distinct()


class InterestedInMyProjectsFilter(UserListFilter):
    """Кто добавил мои проекты к себе в избранное."""

    key = "interested-in-my-projects"

    def apply(self, queryset, current_user):
        return queryset.filter(
            favorites__in=current_user.owned_projects.all(),
        ).distinct()


class ParticipantsOfMyProjectsFilter(UserListFilter):
    """Те, кто стал участником моих проектов (не считая меня самого)."""

    key = "participants-of-my-projects"

    def apply(self, queryset, current_user):
        return (
            queryset.filter(
                participated_projects__in=current_user.owned_projects.all(),
            )
            .exclude(pk=current_user.pk)
            .distinct()
        )


_FILTER_CLASSES = (
    FavoriteOwnersFilter,
    JoinedProjectOwnersFilter,
    InterestedInMyProjectsFilter,
    ParticipantsOfMyProjectsFilter,
)

FILTERS_REGISTRY = {cls.key: cls() for cls in _FILTER_CLASSES}


def apply_filter(queryset, key: str, current_user):
    """Возвращает отфильтрованный queryset или исходный, если ключ не найден."""
    chosen = FILTERS_REGISTRY.get(key)
    if chosen is None:
        return queryset
    return chosen.apply(queryset, current_user)
