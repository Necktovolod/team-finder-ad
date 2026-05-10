"""Management-команда для наполнения БД демо-данными.

Источник данных — JSON-файл, путь по умолчанию
``users/management/commands/data/seed.json``. Можно подсунуть
свой файл флагом ``--file``::

    python manage.py seed_data --file path/to/custom.json
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from projects.models import Project
from users.models import User

DEFAULT_DATA_FILE = Path(__file__).parent / "data" / "seed.json"


class Command(BaseCommand):
    help = "Заполнить БД демо-пользователями и проектами из JSON-файла."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            default=DEFAULT_DATA_FILE,
            help="Путь до JSON-файла с данными.",
        )

    def handle(self, *args, **options):
        path: Path = options["file"]
        if not path.exists():
            raise CommandError(f"Файл данных не найден: {path}")

        payload = json.loads(path.read_text(encoding="utf-8"))

        self._import_users(payload.get("users", []))
        self._import_projects(payload.get("projects", []))
        self._import_superuser(payload.get("superuser"))

        self.stdout.write(self.style.SUCCESS("Готово."))

    # ---------- helpers ----------

    def _import_users(self, items):
        for record in items:
            user, created = User.objects.get_or_create(
                email=record["email"],
                defaults={
                    "name": record["name"],
                    "surname": record["surname"],
                    "phone": record.get("phone") or None,
                    "about": record.get("about", ""),
                    "github_url": record.get("github_url", ""),
                },
            )
            if created:
                user.set_password(record["password"])
                user.save()
                self._success(f"Пользователь {user.email}")
            else:
                self.stdout.write(f"Пользователь {user.email} уже есть")

    def _import_projects(self, items):
        for record in items:
            owner = User.objects.get(email=record["owner_email"])
            project, created = Project.objects.get_or_create(
                name=record["name"],
                owner=owner,
                defaults={
                    "description": record.get("description", ""),
                    "status": record.get("status", "open"),
                    "github_url": record.get("github_url", ""),
                },
            )
            project.participants.add(owner)
            if created:
                self._success(f"Проект «{project.name}»")
            else:
                self.stdout.write(f"Проект «{project.name}» уже есть")

    def _import_superuser(self, record):
        if not record:
            return
        if User.objects.filter(is_superuser=True).exists():
            return
        User.objects.create_superuser(
            email=record["email"],
            password=record["password"],
            name=record["name"],
            surname=record["surname"],
        )
        self._success(
            f"Суперпользователь {record['email']} / {record['password']}",
        )

    def _success(self, message: str) -> None:
        self.stdout.write(self.style.SUCCESS(message))
