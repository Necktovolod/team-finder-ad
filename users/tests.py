"""Тесты пользовательских вьюх и модели."""
from __future__ import annotations

from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from .models import User


class UserBehaviourTests(TestCase):
    """Поведение модели User: автогенерация, нормализация, суперюзер."""

    def test_avatar_is_created_on_save(self) -> None:
        person = User.objects.create_user(
            email="alpha@example.com",
            password="qwerty12345",
            name="Кирилл",
            surname="Сазонов",
        )
        self.assertTrue(person.avatar.name)
        self.assertTrue(person.check_password("qwerty12345"))

    def test_phone_normalisation_in_save(self) -> None:
        person = User.objects.create_user(
            email="phone@example.com",
            password="qwerty12345",
            name="Phone",
            surname="Owner",
            phone="89991234567",
        )
        self.assertEqual(person.phone, "+79991234567")

    def test_canonical_phone_helper(self) -> None:
        with self.subTest("8-formatted"):
            self.assertEqual(
                User.canonical_phone("89991234567"), "+79991234567",
            )
        with self.subTest("already canonical"):
            self.assertEqual(
                User.canonical_phone("+79991234567"), "+79991234567",
            )
        with self.subTest("None"):
            self.assertIsNone(User.canonical_phone(None))

    def test_superuser_flags(self) -> None:
        admin = User.objects.create_superuser(
            email="root@example.com",
            password="qwerty12345",
            name="Root",
            surname="Admin",
        )
        self.assertTrue(admin.is_staff and admin.is_superuser)


class AuthEndpointsTests(TestCase):
    """Регистрация, логин, логаут, неверный пароль."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.member = User.objects.create_user(
            email="member@example.com",
            password="qwerty12345",
            name="Member",
            surname="Existing",
        )

    def test_signup_creates_user_and_redirects_to_login(self) -> None:
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "New",
                "surname": "Comer",
                "email": "fresh@example.com",
                "password": "qwerty12345",
            },
        )
        self.assertRedirects(response, reverse("users:login"))
        self.assertTrue(
            User.objects.filter(email="fresh@example.com").exists(),
        )

    def test_signup_rejects_duplicate_email(self) -> None:
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Dup",
                "surname": "Mail",
                "email": "member@example.com",
                "password": "qwerty12345",
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "уже существует")

    def test_login_then_logout(self) -> None:
        response = self.client.post(
            reverse("users:login"),
            {"email": "member@example.com", "password": "qwerty12345"},
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.client.get(reverse("users:logout"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_login_with_wrong_password(self) -> None:
        response = self.client.post(
            reverse("users:login"),
            {"email": "member@example.com", "password": "incorrect"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Неверный")


class ProfileEditTests(TestCase):
    """Редактирование собственного профиля."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.member = User.objects.create_user(
            email="editor@example.com",
            password="qwerty12345",
            name="Edit",
            surname="Or",
        )
        cls.editor_client = Client()
        cls.editor_client.force_login(cls.member)

    def test_rejects_non_github_url(self) -> None:
        response = self.editor_client.post(
            reverse("users:edit_profile"),
            {
                "name": "Edit",
                "surname": "Or",
                "github_url": "https://gitlab.com/x",
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "github")

    def test_phone_is_normalised(self) -> None:
        self.editor_client.post(
            reverse("users:edit_profile"),
            {
                "name": "Edit",
                "surname": "Or",
                "phone": "89998887766",
                "github_url": "https://github.com/me",
            },
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.phone, "+79998887766")
