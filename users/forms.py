"""Формы пользователей: регистрация, логин, профиль, смена пароля."""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm

from .constants import FIRST_NAME_LENGTH, LAST_NAME_LENGTH
from .models import User
from .services import to_canonical_phone


class RegistrationForm(forms.ModelForm):
    """Форма регистрации нового пользователя."""

    name = forms.CharField(label="Имя", max_length=FIRST_NAME_LENGTH)
    surname = forms.CharField(label="Фамилия", max_length=LAST_NAME_LENGTH)
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Пользователь с таким email уже существует",
            )
        return email

    def save(self, commit=True):
        return User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            name=self.cleaned_data["name"],
            surname=self.cleaned_data["surname"],
        )


class AuthForm(forms.Form):
    """Форма входа: email + пароль."""

    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            user = authenticate(
                self.request, username=email, password=password,
            )
            if user is None:
                raise forms.ValidationError("Неверный имейл или пароль")
            self.user = user
        return cleaned


class UpdateProfileForm(forms.ModelForm):
    """Форма редактирования профиля владельцем."""

    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
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
        canonical = to_canonical_phone(raw)
        clashes = User.objects.filter(phone=canonical)
        if self.instance.pk:
            clashes = clashes.exclude(pk=self.instance.pk)
        if clashes.exists():
            raise forms.ValidationError(
                "Этот номер телефона уже используется",
            )
        return canonical


class PasswordUpdateForm(PasswordChangeForm):
    """Алиас для штатной формы смены пароля."""
