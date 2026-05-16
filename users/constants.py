"""Константы приложения users."""

# Длины полей модели User.
EMAIL_MAX_LENGTH = 254
NAME_MAX_LENGTH = 124
SURNAME_MAX_LENGTH = 124
PHONE_MAX_LENGTH = 12
ABOUT_MAX_LENGTH = 256

# Пагинация списка пользователей.
USERS_PER_PAGE = 12

# Параметры генерации placeholder-аватара.
AVATAR_SIDE_PX = 256
AVATAR_FONT_RATIO = 0.55
AVATAR_FONT_FILE = "DejaVuSans-Bold.ttf"
AVATAR_FALLBACK_LETTER = "?"
AVATAR_TEXT_COLOR = "white"
AVATAR_TEXT_ANCHOR = (0, 0)

# Размер миниатюры аватара в админке.
ADMIN_AVATAR_THUMB_PX = 32
