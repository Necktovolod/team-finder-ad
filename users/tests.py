"""Тесты приложения users."""
from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from .models import User
from .services import to_canonical_phone


class UserModelTestCase(TestCase):
    """Базовые проверки кастомной модели User."""

    def test_avatar_is_generated_on_create(self):
        user = User.objects.create_user(
            email="alpha@example.com",
            password="qwerty12345",
            name="Алиса",
            surname="Альфова",
        )
        self.assertTrue(user.avatar.name)
        self.assertTrue(user.check_password("qwerty12345"))

    def test_phone_is_canonicalised_on_save(self):
        user = User.objects.create_user(
            email="beta@example.com",
            password="qwerty12345",
            name="Бета",
            surname="Бетова",
            phone="89991234567",
        )
        self.assertEqual(user.phone, "+79991234567")

    def test_to_canonical_phone(self):
        self.assertEqual(to_canonical_phone("89991234567"), "+79991234567")
        self.assertEqual(to_canonical_phone("+79991234567"), "+79991234567")
        self.assertIsNone(to_canonical_phone(None))

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="root@example.com",
            password="rootroot1234",
            name="Root",
            surname="Admin",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AuthFlowTestCase(TestCase):
    """Сценарии регистрации, входа и выхода."""

    @classmethod
    def setUpTestData(cls):
        cls.existing_user = User.objects.create_user(
            email="login@example.com",
            password="qwerty12345",
            name="Существующий",
            surname="Пользователь",
        )

    def test_signup_redirects_to_login_page(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Новый",
                "surname": "Юзер",
                "email": "newcomer@example.com",
                "password": "qwerty12345",
            },
        )
        self.assertRedirects(response, reverse("users:login"))
        self.assertTrue(
            User.objects.filter(email="newcomer@example.com").exists(),
        )

    def test_signup_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Дубль",
                "surname": "Юзер",
                "email": "login@example.com",
                "password": "qwerty12345",
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "уже существует")

    def test_login_then_logout(self):
        response = self.client.post(
            reverse("users:login"),
            {"email": "login@example.com", "password": "qwerty12345"},
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.client.get(reverse("users:logout"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_login_with_wrong_password(self):
        response = self.client.post(
            reverse("users:login"),
            {"email": "login@example.com", "password": "incorrect"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Неверный")


class ProfileEditTestCase(TestCase):
    """Сценарии редактирования собственного профиля."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="editor@example.com",
            password="qwerty12345",
            name="Редактор",
            surname="Профилев",
        )
        cls.editor_client = Client()
        cls.editor_client.force_login(cls.user)

    def test_non_github_url_is_rejected(self):
        response = self.editor_client.post(
            reverse("users:edit_profile"),
            {
                "name": "Редактор",
                "surname": "Профилев",
                "github_url": "https://gitlab.com/me",
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "github")

    def test_phone_is_normalised_on_edit(self):
        self.editor_client.post(
            reverse("users:edit_profile"),
            {
                "name": "Редактор",
                "surname": "Профилев",
                "phone": "89998887766",
                "github_url": "https://github.com/me",
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79998887766")
