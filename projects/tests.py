"""Тесты приложения projects."""
import json
from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from users.models import User

from .constants import PROJECT_STATUS_CLOSED, PROJECT_STATUS_OPEN
from .models import Project


class PublicPagesTestCase(TestCase):
    """Доступ к публичным страницам у неавторизованного гостя."""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            email="author@example.com",
            password="qwerty12345",
            name="Автор",
            surname="Проектов",
        )
        cls.project = Project.objects.create(
            name="Демонстрационный проект",
            description="Описание",
            owner=cls.author,
        )

    def test_anonymous_sees_project_list(self):
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_anonymous_sees_project_detail(self):
        response = self.client.get(
            reverse("projects:detail", args=[self.project.pk]),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_anonymous_redirected_from_create_page(self):
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(reverse("users:login"), response["Location"])


class ProjectCreationTestCase(TestCase):
    """Создание проекта авторизованным пользователем."""

    @classmethod
    def setUpTestData(cls):
        cls.creator = User.objects.create_user(
            email="creator@example.com",
            password="qwerty12345",
            name="Создатель",
            surname="Проектов",
        )
        cls.creator_client = Client()
        cls.creator_client.force_login(cls.creator)

    def test_owner_and_participant_are_set(self):
        response = self.creator_client.post(
            reverse("projects:create"),
            {
                "name": "Новый проект",
                "description": "что-то новое",
                "github_url": "https://github.com/creator/repo",
                "status": PROJECT_STATUS_OPEN,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        project = Project.objects.get(name="Новый проект")
        self.assertEqual(project.owner, self.creator)
        self.assertIn(self.creator, project.participants.all())

    def test_non_github_url_is_rejected(self):
        response = self.creator_client.post(
            reverse("projects:create"),
            {
                "name": "Bad URL",
                "description": "что-то",
                "github_url": "https://gitlab.com/x",
                "status": PROJECT_STATUS_OPEN,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "github")


class AjaxEndpointsTestCase(TestCase):
    """AJAX-эндпоинты избранного, участия и завершения проекта."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="ajax_owner@example.com",
            password="qwerty12345",
            name="AjaxOwner",
            surname="Q",
        )
        cls.guest = User.objects.create_user(
            email="ajax_guest@example.com",
            password="qwerty12345",
            name="AjaxGuest",
            surname="Q",
        )
        cls.owner_client = Client()
        cls.owner_client.force_login(cls.owner)
        cls.guest_client = Client()
        cls.guest_client.force_login(cls.guest)

    def setUp(self):
        # Свежий проект на каждый тест: статус мутируется в test_complete.
        self.project = Project.objects.create(
            name="AJAX target",
            owner=self.owner,
        )

    def _post_json(self, client, url):
        response = client.post(url)
        self.assertEqual(response["Content-Type"], "application/json")
        return response.status_code, json.loads(response.content)

    def test_toggle_favorite_round_trip(self):
        url = reverse("projects:toggle_favorite", args=[self.project.pk])
        status, data = self._post_json(self.guest_client, url)
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(data["favorited"])
        status, data = self._post_json(self.guest_client, url)
        self.assertFalse(data["favorited"])

    def test_toggle_participate_round_trip(self):
        url = reverse("projects:toggle_participate", args=[self.project.pk])
        status, data = self._post_json(self.guest_client, url)
        self.assertTrue(data["participant"])
        status, data = self._post_json(self.guest_client, url)
        self.assertFalse(data["participant"])

    def test_complete_only_for_owner(self):
        url = reverse("projects:complete", args=[self.project.pk])
        response = self.guest_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        response = self.owner_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, PROJECT_STATUS_CLOSED)


class FavoritesAndFiltersTestCase(TestCase):
    """Страница «Избранное» и фильтр пользователей."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="me@example.com",
            password="qwerty12345",
            name="Я",
            surname="Сам",
        )
        cls.peer = User.objects.create_user(
            email="peer@example.com",
            password="qwerty12345",
            name="UnusualPeerLabel",
            surname="UnusualPeerSurname",
        )
        cls.peer_project = Project.objects.create(
            name="Проект коллеги",
            owner=cls.peer,
        )
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)

    def test_favorites_page_shows_added_projects(self):
        self.user.favorites.add(self.peer_project)
        response = self.user_client.get(reverse("projects:favorites"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Проект коллеги")

    def test_filter_owners_of_favorite_projects(self):
        self.user.favorites.add(self.peer_project)
        response = self.user_client.get(
            reverse("users:list") + "?filter=owners-of-favorite-projects",
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "UnusualPeerLabel")
