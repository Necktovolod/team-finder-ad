"""Маршруты приложения users."""
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("list/", views.participants_page, name="list"),
    path("register/", views.register_page, name="register"),
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("edit-profile/", views.edit_profile_page, name="edit_profile"),
    path(
        "change-password/",
        views.change_password_page,
        name="change_password",
    ),
    path("<int:pk>/", views.profile_page, name="detail"),
]
