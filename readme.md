# TeamFinder

Платформа для поиска тиммейтов на pet-проекты. Реализован вариант 1
(избранное + фильтрация пользователей по 4 признакам).

В качестве вьюх везде используются **Class-Based Views** —
наследники `ListView`, `DetailView`, `CreateView`, `UpdateView`
и `View` (для AJAX-эндпоинтов). Для логина/логаута/смены пароля
переиспользуются готовые `django.contrib.auth.views`.

## Зависимости

- Python 3.11
- Django 5.2.4
- PostgreSQL 16
- Pillow
- python-decouple

## Запуск локально

```bash
git clone https://github.com/Necktovolod/team-finder-ad.git
cd team-finder-ad

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env_example .env              # отредактировать при необходимости

docker compose up -d              # PostgreSQL
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

После этого сайт открыт на `http://localhost:8000/`.

## Переменные окружения

| Имя                    | Описание                                         |
|------------------------|--------------------------------------------------|
| `DJANGO_SECRET_KEY`    | секретный ключ                                   |
| `DJANGO_DEBUG`         | `True` для разработки                            |
| `DJANGO_ALLOWED_HOSTS` | список хостов через запятую                      |
| `POSTGRES_DB`          | имя БД                                           |
| `POSTGRES_USER`        | пользователь                                     |
| `POSTGRES_PASSWORD`    | пароль                                           |
| `POSTGRES_HOST`        | хост (`localhost` для локальной разработки)      |
| `POSTGRES_PORT`        | порт                                             |

## Демо-учётки

| Email                     | Пароль        | Роль          |
|---------------------------|---------------|---------------|
| `admin@example.com`       | `admin12345`  | администратор |
| `kirill@yandex.ru`        | `qwerty12345` | пользователь  |
| `elena@example.com`       | `qwerty12345` | пользователь  |
| `artem@example.com`       | `qwerty12345` | пользователь  |
| `viktoriya@example.com`   | `qwerty12345` | пользователь  |

## Что реализовано

- кастомный `User` (email вместо username), валидация через
  `RegexValidator`;
- автогенерация placeholder-аватарки в `User.save()`;
- проверка телефона и его нормализация (`8XXXXXXXXXX` → `+7XXXXXXXXXX`)
  через `User.canonical_phone`;
- проверка ссылки на `github.com` для пользователей и проектов;
- `Project.Status` как `TextChoices`, `Project.is_open` — property;
- list-страницы используют `paginate_by = 12`;
- AJAX-эндпоинты — `View`-наследники с декоратором `@require_POST`;
- логин/логаут/смена пароля — `django.contrib.auth.views`-наследники;
- список пользователей с 4 фильтрами по `?filter=...`.

## Запуск тестов

```bash
python manage.py test users projects
```

В наборе 20 тестов: модель, формы, регистрация, логин/логаут, профиль,
создание/редактирование проекта, AJAX-эндпоинты, страница «Избранное»,
фильтр пользователей.

## Линтер

```bash
pip install flake8
flake8 users projects team_finder
```

Конфиг — в `setup.cfg`, лимит длины строки 100.

## Автор

[Necktovolod](https://github.com/Necktovolod)
