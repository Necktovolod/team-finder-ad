"""Генерация placeholder-аватарок (буква на цветном фоне)."""
import io
import secrets

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

from .constants import (
    AVATAR_BACKGROUNDS,
    AVATAR_FALLBACK_LETTER,
    AVATAR_FONT_NAME,
    AVATAR_FONT_RATIO,
    AVATAR_SIDE_PX,
    AVATAR_TEXT_ANCHOR,
    AVATAR_TEXT_COLOR,
)


def _pick_background() -> str:
    """Случайно выбирает один из заранее заготовленных цветов фона."""
    return secrets.choice(AVATAR_BACKGROUNDS)


def _load_font(side: int) -> ImageFont.ImageFont:
    """Подгружает TTF-шрифт нужного размера, иначе откатывается на дефолт."""
    try:
        return ImageFont.truetype(
            AVATAR_FONT_NAME, size=int(side * AVATAR_FONT_RATIO),
        )
    except OSError:
        return ImageFont.load_default()


def render_avatar(
    seed_letter: str, side: int = AVATAR_SIDE_PX,
) -> ContentFile:
    """Возвращает PNG-аватарку: первая буква на однотонном фоне."""
    canvas = Image.new("RGB", (side, side), color=_pick_background())
    pen = ImageDraw.Draw(canvas)

    char = (seed_letter or AVATAR_FALLBACK_LETTER)[0].upper()
    font = _load_font(side)

    box = pen.textbbox(AVATAR_TEXT_ANCHOR, char, font=font)
    text_w, text_h = box[2] - box[0], box[3] - box[1]
    x = (side - text_w) / 2 - box[0]
    y = (side - text_h) / 2 - box[1]
    pen.text((x, y), char, fill=AVATAR_TEXT_COLOR, font=font)

    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    buffer.seek(0)
    return ContentFile(buffer.getvalue())
