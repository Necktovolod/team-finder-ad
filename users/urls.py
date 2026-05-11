"""URL-маршруты приложения users."""
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("list/", views.UserListView.as_view(), name="list"),
    path("register/", views.SignupView.as_view(), name="register"),
    path("login/", views.TeamFinderLoginView.as_view(), name="login"),
    path("logout/", views.TeamFinderLogoutView.as_view(), name="logout"),
    path(
        "edit-profile/",
        views.ProfileEditView.as_view(),
        name="edit_profile",
    ),
    path(
        "change-password/",
        views.TeamFinderPasswordChangeView.as_view(),
        name="change_password",
    ),
    path("<int:pk>/", views.UserDetailView.as_view(), name="detail"),
]
