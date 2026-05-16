"""Вспомогательные сервисные функции приложения users."""
from __future__ import annotations

import io
import secrets
from enum import StrEnum

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

from .constants import (
    AVATAR_FALLBACK_LETTER,
    AVATAR_FONT_FILE,
    AVATAR_FONT_RATIO,
    AVATAR_SIDE_PX,
    AVATAR_TEXT_ANCHOR,
    AVATAR_TEXT_COLOR,
)


class AvatarPalette(StrEnum):
    """Палитра фоновых заливок для placeholder-аватарок."""

    OCEAN_BLUE = "#385F8E"
    LAVENDER = "#7B5FA8"
    EMERALD = "#3F9A6F"
    AMBER = "#C58145"
    PINK_CORAL = "#B95C73"
    TEAL = "#369494"
    SLATE = "#677484"
    PLUM = "#946595"
    FOREST = "#4D7548"
    BURNT_ORANGE = "#A8623F"


# Готовый кортеж для secrets.choice (порядок не важен).
AVATAR_BACKGROUNDS = tuple(color.value for color in AvatarPalette)


def _load_font(side: int) -> ImageFont.ImageFont:
    """Подгружает TTF-шрифт нужного размера; при ошибке —
    встроенный bitmap-шрифт того же размера (Pillow 10+
    позволяет передать size в load_default)."""
    target_size = int(side * AVATAR_FONT_RATIO)
    try:
        return ImageFont.truetype(AVATAR_FONT_FILE, size=target_size)
    except OSError:
        try:
            return ImageFont.load_default(size=target_size)
        except TypeError:
            # Pillow < 10 не принимает size в load_default —
            # возвращаем дефолтный bitmap.
            return ImageFont.load_default()


def build_placeholder_avatar(
    letter: str, side: int = AVATAR_SIDE_PX,
) -> ContentFile:
    """Возвращает PNG-аватарку: одна заглавная буква на однотонном фоне."""
    canvas = Image.new(
        "RGB", (side, side), color=secrets.choice(AVATAR_BACKGROUNDS),
    )
    pen = ImageDraw.Draw(canvas)

    char = (letter or AVATAR_FALLBACK_LETTER)[0].upper()
    font = _load_font(side)

    box = pen.textbbox(AVATAR_TEXT_ANCHOR, char, font=font)
    text_w, text_h = box[2] - box[0], box[3] - box[1]
    pen.text(
        ((side - text_w) / 2 - box[0], (side - text_h) / 2 - box[1]),
        char,
        fill=AVATAR_TEXT_COLOR,
        font=font,
    )

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)
    return ContentFile(buf.getvalue())
