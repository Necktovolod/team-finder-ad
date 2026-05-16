"""Команда ``manage.py seed_data`` — заполняет БД демо-объектами из JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from projects.models import Project
from users.models import User

DEFAULT_DATA_FILE = Path(__file__).parent / "data" / "seed.json"


class Command(BaseCommand):
    help = "Заполнить БД демо-данными из JSON-файла."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            default=DEFAULT_DATA_FILE,
            help="JSON-файл с данными",
        )

    def handle(self, *args, **opts):
        source: Path = opts["file"]
        if not source.exists():
            raise CommandError(f"Файл данных не найден: {source}")

        with source.open(encoding="utf-8") as fh:
            payload = json.load(fh)

        for line in self._import_users(payload.get("users", ())):
            self.stdout.write(self.style.SUCCESS(line))
        for line in self._import_projects(payload.get("projects", ())):
            self.stdout.write(self.style.SUCCESS(line))
        if (admin := payload.get("superuser")):
            self.stdout.write(
                self.style.SUCCESS(self._import_admin(admin)),
            )

        self.stdout.write(self.style.SUCCESS("Готово."))

    # --- внутренности ---

    @staticmethod
    def _import_users(records) -> Iterable[str]:
        for r in tqdm(list(records), desc="Пользователи"):
            user, fresh = User.objects.get_or_create(
                email=r["email"],
                defaults={
                    "name": r["name"],
                    "surname": r["surname"],
                    "phone": r.get("phone") or None,
                    "about": r.get("about", ""),
                    "github_url": r.get("github_url", ""),
                },
            )
            if fresh:
                user.set_password(r["password"])
                user.save()
                yield f"Пользователь {user.email}"
            else:
                yield f"Уже существует: {user.email}"

    @staticmethod
    def _import_projects(records) -> Iterable[str]:
        for r in tqdm(list(records), desc="Проекты"):
            owner = User.objects.get(email=r["owner_email"])
            project, fresh = Project.objects.get_or_create(
                name=r["name"],
                owner=owner,
                defaults={
                    "description": r.get("description", ""),
                    "status": r.get("status", Project.Status.OPEN),
                    "github_url": r.get("github_url", ""),
                },
            )
            project.participants.add(owner)
            yield (
                f"Проект «{project.name}»"
                if fresh
                else f"Уже существует: «{project.name}»"
            )

    @staticmethod
    def _import_admin(record) -> str:
        if User.objects.filter(is_superuser=True).exists():
            return "Суперюзер уже есть"
        User.objects.create_superuser(
            email=record["email"],
            password=record["password"],
            name=record["name"],
            surname=record["surname"],
        )
        return f"Суперюзер {record['email']} / {record['password']}"
