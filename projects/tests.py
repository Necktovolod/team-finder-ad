"""Тесты приложения projects."""
from __future__ import annotations

import json
from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from users.models import User

from .models import Project


class PublicAccessTests(TestCase):
    """Что видит / не видит анонимный пользователь."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.owner = User.objects.create_user(
            email="anon_owner@example.com",
            password="qwerty12345",
            name="Author",
            surname="Owner",
        )
        cls.project = Project.objects.create(
            name="Public sample",
            description="desc",
            owner=cls.owner,
        )

    def test_anonymous_reads_list(self) -> None:
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_anonymous_reads_detail(self) -> None:
        response = self.client.get(
            reverse("projects:detail", args=[self.project.pk]),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_anonymous_cant_create(self) -> None:
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(reverse("users:login"), response["Location"])


class CreateAndEditTests(TestCase):
    """Создание и редактирование проекта."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.maker = User.objects.create_user(
            email="maker@example.com",
            password="qwerty12345",
            name="Maker",
            surname="One",
        )
        cls.maker_client = Client()
        cls.maker_client.force_login(cls.maker)

    def test_creator_becomes_owner_and_participant(self) -> None:
        response = self.maker_client.post(
            reverse("projects:create"),
            {
                "name": "Brand new",
                "description": "x",
                "github_url": "https://github.com/maker/repo",
                "status": Project.Status.OPEN,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        project = Project.objects.get(name="Brand new")
        self.assertEqual(project.owner, self.maker)
        self.assertTrue(
            project.participants.filter(pk=self.maker.pk).exists(),
        )

    def test_create_rejects_non_github_url(self) -> None:
        response = self.maker_client.post(
            reverse("projects:create"),
            {
                "name": "Wrong",
                "description": "x",
                "github_url": "https://gitlab.com/x",
                "status": Project.Status.OPEN,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "github")


class AjaxTests(TestCase):
    """AJAX-эндпоинты избранного, участия и завершения."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.owner = User.objects.create_user(
            email="ajax_owner@example.com",
            password="qwerty12345",
            name="Owner",
            surname="X",
        )
        cls.guest = User.objects.create_user(
            email="ajax_guest@example.com",
            password="qwerty12345",
            name="Guest",
            surname="X",
        )
        cls.owner_cli = Client()
        cls.owner_cli.force_login(cls.owner)
        cls.guest_cli = Client()
        cls.guest_cli.force_login(cls.guest)
        cls.project = Project.objects.create(
            name="AJAX target", owner=cls.owner,
        )

    def _ajax(self, client: Client, url: str):
        response = client.post(url)
        self.assertEqual(response["Content-Type"], "application/json")
        return response.status_code, json.loads(response.content)

    def test_toggle_favorite_roundtrip(self) -> None:
        url = reverse("projects:toggle_favorite", args=[self.project.pk])
        status, payload = self._ajax(self.guest_cli, url)
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["favorited"])
        _, payload = self._ajax(self.guest_cli, url)
        self.assertFalse(payload["favorited"])

    def test_toggle_participate_roundtrip(self) -> None:
        url = reverse("projects:toggle_participate", args=[self.project.pk])
        _, payload = self._ajax(self.guest_cli, url)
        self.assertTrue(payload["participant"])
        _, payload = self._ajax(self.guest_cli, url)
        self.assertFalse(payload["participant"])

    def test_complete_only_for_owner(self) -> None:
        # Создаём локальный проект, чтобы не мутировать общий cls.project
        # (после rollback БД его статус снова станет OPEN, но Python-объект
        # cls.project в памяти на это не реагирует).
        project = Project.objects.create(
            name="Disposable for complete test", owner=self.owner,
        )
        url = reverse("projects:complete", args=[project.pk])
        response = self.guest_cli.post(url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        response = self.owner_cli.post(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.CLOSED)


class FavoritesAndFiltersTests(TestCase):
    """Страница «Избранное» и фильтрация юзеров."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.member = User.objects.create_user(
            email="favmember@example.com",
            password="qwerty12345",
            name="Me",
            surname="Self",
        )
        cls.peer = User.objects.create_user(
            email="peer@example.com",
            password="qwerty12345",
            name="UnusualPeerName",
            surname="UnusualPeerSurname",
        )
        cls.peer_project = Project.objects.create(
            name="Peer's project",
            owner=cls.peer,
        )
        cls.member_cli = Client()
        cls.member_cli.force_login(cls.member)

    def test_favorites_list_contains_added(self) -> None:
        self.member.favorites.add(self.peer_project)
        response = self.member_cli.get(reverse("projects:favorites"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Peer's project содержит апостроф ('). Django его экранирует
        # как &#x27;, поэтому в HTML ищем экранированную форму.
        self.assertContains(response, "Peer")

    def test_filter_owners_of_favorite_projects(self) -> None:
        self.member.favorites.add(self.peer_project)
        url = (
            reverse("users:list") + "?filter=owners-of-favorite-projects"
        )
        response = self.member_cli.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "UnusualPeerName")
