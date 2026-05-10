"""Корневая маршрутизация проекта."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def home_redirect(request):
    """Главная страница перенаправляет на список проектов."""
    return redirect("projects:list")


urlpatterns = [
    path("", home_redirect),
    path("admin/", admin.site.urls),
    path("projects/", include("projects.urls")),
    path("users/", include("users.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
