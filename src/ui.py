"""UI: text and buttons for the menus and screens, with the Czech letters (raylib's own font has none).

    ui.draw_text("Opravdu chcete odejít?", x, y, 30, color)   # screen pixels
    ui.text_width(msg, 30)
    ui.draw_centered(msg, cx, y, 30, color)                   # centred on cx, top at y
    if ui.button(rect, "Zpět", 30): ...                       # draws a menu button; True on the frame it is clicked
    ui.unload()                                               # before close_window

The font is the first of UI_FONTS that exists, loaded the first time it is needed; without one the letters lose
their accents (`plain`).
"""
from __future__ import annotations

import unicodedata

import pyray as pr

from .config import UI_FONTS

CZECH: str = "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"
# ASCII but "|" (too tall in Consolas: raylib warns) + the Czech letters: everything the font has
CHARS: str = "".join(chr(c) for c in range(32, 127) if c != ord("|")) + CZECH
FONT_SIZE: int = 48   # loaded at; drawn at any size

# The menu's colours (the title's letters and frame on the menu pictures)
GREEN: pr.Color = pr.Color(139, 189, 85, 255)
DARK_GREEN: pr.Color = pr.Color(27, 61, 27, 255)
BUTTON_FILL: pr.Color = pr.Color(18, 22, 18, 200)
DIM: pr.Color = pr.Color(100, 125, 85, 255)
PANEL: pr.Color = pr.Color(12, 15, 12, 230)

_font: pr.Font | None = None
_loaded: bool = False


def plain(text: str) -> str:
    """`text` without accents (for raylib's own font, and the console, which may not take UTF-8)."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


def font() -> pr.Font | None:
    """The first of UI_FONTS that exists, with CHARS; None if there is none."""
    global _font, _loaded
    if not _loaded:
        _loaded = True
        for path in UI_FONTS:
            if path.is_file():
                codepoints = [ord(c) for c in CHARS]
                array = pr.ffi.new("int[]", codepoints)   # pyray wants a plain int *, kept alive while it loads
                _font = pr.load_font_ex(str(path), FONT_SIZE, pr.ffi.cast("int *", array), len(codepoints))
                pr.set_texture_filter(_font.texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)
                break
    return _font


def text_width(msg: str, size: float) -> float:
    f = font()
    if f is None:
        return pr.measure_text(plain(msg), int(size))
    return pr.measure_text_ex(f, msg, size, 1).x


def draw_text(msg: str, x: float, y: float, size: float, color: pr.Color) -> None:
    f = font()
    if f is None:
        pr.draw_text(plain(msg), int(x), int(y), int(size), color)
    else:
        pr.draw_text_ex(f, msg, pr.Vector2(x, y), size, 1, color)


def draw_centered(msg: str, cx: float, y: float, size: float, color: pr.Color) -> None:
    draw_text(msg, cx - text_width(msg, size) / 2, y, size, color)


def button(rect: pr.Rectangle, label: str, size: float, border: float = 3.0) -> bool:
    """A menu button: highlighted under the mouse. True on the frame it is clicked."""
    on = pr.check_collision_point_rec(pr.get_mouse_position(), rect)
    pr.draw_rectangle_rec(rect, GREEN if on else BUTTON_FILL)
    pr.draw_rectangle_lines_ex(rect, border, DARK_GREEN if on else DIM)
    draw_centered(label, rect.x + rect.width / 2, rect.y + (rect.height - size) / 2, size,
                  DARK_GREEN if on else GREEN)
    return on and pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT)


def unload() -> None:
    global _font, _loaded
    if _font is not None:
        pr.unload_font(_font)
    _font, _loaded = None, False
