# 🤝 TeamFinder

> Веб-платформа для поиска тиммейтов на pet-проекты.
> Авторы публикуют идеи, остальные пользователи добавляют их в
> избранное и присоединяются как участники.

📦 Реализован **Вариант 1**: «Избранное» + фильтрация пользователей по
4 критериям (фавориты автора, общие проекты и т. д.).

---

## 🛠 Стек

| Слой         | Технологии                                |
|--------------|-------------------------------------------|
| Backend      | Python 3.11, Django 5.2.4                 |
| База данных  | PostgreSQL 16 (поднимается через Docker)  |
| Изображения  | Pillow (генератор аватарок-плейсхолдеров) |
| Конфиг       | python-decouple (значения из `.env`)      |

---

## 📁 Структура проекта

```
team-finder-ad/
├── team_finder/        # настройки Django, корневые URL и WSGI/ASGI
├── users/              # модель User, валидаторы, фильтры, формы, вьюхи
│   ├── constants.py    # длины полей, палитра аватаров и т. п.
│   ├── validators.py   # phone_format_validator, github_link_validator
│   ├── services.py     # to_canonical_phone и другие хелперы
│   ├── filters.py      # классы-стратегии фильтрации списка юзеров
│   └── …
├── projects/           # модель Project, CRUD, AJAX, избранное
│   ├── constants.py    # статусы, лимиты, размер страницы
│   ├── services.py     # paginate, base_project_queryset, with_related
│   └── …
├── templates_var1/     # HTML-шаблоны (вариант 1)
├── static/             # CSS, JS, шрифты, картинки
└── docker-compose.yml  # сервис PostgreSQL
```

---

## 🚀 Запуск

### 1. Клонирование
```bash
git clone https://github.com/Necktovolod/team-finder-ad.git
cd team-finder-ad
```

### 2. Виртуальное окружение
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Конфиг
```bash
cp .env_example .env
# → отредактировать значения при необходимости
```

### 4. PostgreSQL через Docker
```bash
docker compose up -d
```

### 5. Миграции и демо-данные
```bash
python manage.py migrate
python manage.py seed_data
```

### 6. Сервер разработки
```bash
python manage.py runserver
# → http://localhost:8000
```

---

## ⚙️ Переменные окружения

| Имя                    | Описание                                             |
|------------------------|------------------------------------------------------|
| `DJANGO_SECRET_KEY`    | секрет Django                                        |
| `DJANGO_DEBUG`         | `True` для разработки                                |
| `DJANGO_ALLOWED_HOSTS` | список хостов через запятую                          |
| `POSTGRES_DB`          | имя базы                                             |
| `POSTGRES_USER`        | пользователь                                         |
| `POSTGRES_PASSWORD`    | пароль                                               |
| `POSTGRES_HOST`        | хост базы (`localhost` для локальной разработки)     |
| `POSTGRES_PORT`        | порт базы                                            |

---

## 👥 Демонстрационные аккаунты

| Email                     | Пароль        | Роль          |
|---------------------------|---------------|---------------|
| `admin@example.com`       | `admin12345`  | администратор |
| `kirill@yandex.ru`        | `qwerty12345` | пользователь  |
| `elena@example.com`       | `qwerty12345` | пользователь  |
| `artem@example.com`       | `qwerty12345` | пользователь  |
| `viktoriya@example.com`   | `qwerty12345` | пользователь  |

---

## ✨ Что реализовано

- 👤 Кастомная модель `User` с email вместо username.
- 🎨 Автогенерация аватарки (буква на цветном фоне) при создании
  пользователя без изображения.
- 📞 Нормализация телефона: `8XXXXXXXXXX` → `+7XXXXXXXXXX`.
- 🔗 Валидация ссылки на GitHub (домен `github.com`).
- 📃 Пагинация по 12 элементов.
- ❤️ Избранное (AJAX): `POST /projects/<id>/toggle-favorite/`.
- 🤝 Участие в проекте (AJAX): `POST /projects/<id>/toggle-participate/`.
- 🏁 Закрытие проекта владельцем (AJAX): `POST /projects/<id>/complete/`.
- 🔎 4 фильтра пользователей на `/users/list/?filter=...`.
- 🧰 Админка с миниатюрой аватарки и списком участников проекта.

---

## ✅ Тесты

```bash
python manage.py test users projects
```

В проекте 20 авто-тестов, покрывающих модели, формы, AJAX-эндпоинты,
страницы и фильтры.

---

## 🧹 Линтер

`flake8` настроен в `setup.cfg` (max-line-length = 100):

```bash
pip install flake8
flake8 users projects team_finder
```

---

## 👨‍💻 Автор

- GitHub: [Necktovolod](https://github.com/Necktovolod)
