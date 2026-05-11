"""Формы приложения users.

Поля форм должны совпадать с тем, что рендерят шаблоны
из ``templates_var1/`` (``form.email``, ``form.password`` и т. п.).
"""
from django import forms
from django.contrib.auth import authenticate

from .models import User


class SignupForm(forms.ModelForm):
    """Регистрация: email + имя + фамилия + пароль."""

    name = forms.CharField(label="Имя", max_length=124)
    surname = forms.CharField(label="Фамилия", max_length=124)
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "name", "surname")

    def clean_email(self):
        value = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=value).exists():
            raise forms.ValidationError(
                "Пользователь с таким email уже существует",
            )
        return value

    def save(self, commit=True):
        return User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            name=self.cleaned_data["name"],
            surname=self.cleaned_data["surname"],
        )


class LoginForm(forms.Form):
    """Простая форма входа: email + пароль."""

    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request
        self.user_cache = None

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            self.user_cache = authenticate(
                self._request, username=email, password=password,
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Неверный имейл или пароль",
                )
        return cleaned


class ProfileEditForm(forms.ModelForm):
    """Изменение профиля владельцем."""

    class Meta:
        model = User
        fields = (
            "name", "surname", "avatar", "about", "phone", "github_url",
        )
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "Ссылка на Github",
        }
        widgets = {"about": forms.Textarea(attrs={"rows": 3})}

    def clean_phone(self):
        raw = self.cleaned_data.get("phone") or ""
        if not raw:
            return raw
        normalised = User.canonical_phone(raw)
        clash = User.objects.filter(phone=normalised)
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError(
                "Этот номер телефона уже используется",
            )
        return normalised
