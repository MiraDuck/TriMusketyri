"""Tutorial: a torn notebook page on the rest room's wall, right of the computer, saying what everything does.

    tutorial = Tutorial(car_pos)   # after init_window; draws the page once
    tutorial.draw(lit)             # inside 3D mode (a draw_scene overlay); lit: its car's lamp is on
    tutorial.unload()

It looks like the posters (ruled paper, binder holes, tape, red and blue marker) but is drawn in code into a render
texture, as there is too much text to paint it: TUTORIAL_TEXT, in the first handwriting font of TUTORIAL_FONTS. A
quad just in front of the wall (TUTORIAL_CORNERS). Not lit by the lamps, so it is drawn dimmer instead, and nearly
dark while its car is.
"""
from __future__ import annotations

import random

import pyray as pr

from . import ui
from .config import (
    TUTORIAL_BLUE, TUTORIAL_CORNERS, TUTORIAL_DARK, TUTORIAL_FONTS, TUTORIAL_LIT, TUTORIAL_PAPER, TUTORIAL_RED,
    TUTORIAL_RULE, TUTORIAL_SIZE, TUTORIAL_TAPE, TUTORIAL_TEXT, TUTORIAL_TITLE,
)
from .screens import draw_quad

FONT_SIZE: int = 72   # loaded at; drawn smaller
MARGIN: int = 60
TOP: int = 66         # the paper starts under the binder holes' teeth
TITLE_SIZE: int = 92
TEXT_SIZE: int = 38
LINE: int = 43        # the ruled lines; the text sits on them
TORN: int = 34


def _load_font() -> pr.Font | None:
    """The first of TUTORIAL_FONTS that exists, with ui's letters; None: use ui's font."""
    for path in TUTORIAL_FONTS:
        if path.is_file():
            codepoints = [ord(c) for c in ui.CHARS]
            array = pr.ffi.new("int[]", codepoints)
            pr.set_trace_log_level(pr.TraceLogLevel.LOG_ERROR)   # handwriting's tall letters each print a warning
            font = pr.load_font_ex(str(path), FONT_SIZE, pr.ffi.cast("int *", array), len(codepoints))
            pr.set_trace_log_level(pr.TraceLogLevel.LOG_WARNING)
            pr.set_texture_filter(font.texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)
            return font
    return None


class Tutorial:
    def __init__(self, car_pos: pr.Vector3) -> None:
        self.corners: list[pr.Vector3] = [pr.vector3_add(car_pos, c) for c in TUTORIAL_CORNERS]
        self.sheet: pr.RenderTexture = pr.load_render_texture(*TUTORIAL_SIZE)
        pr.set_texture_filter(self.sheet.texture, pr.TextureFilter.TEXTURE_FILTER_BILINEAR)
        self.font: pr.Font | None = _load_font()
        self._render()

    def _width(self, msg: str, size: float) -> float:
        return pr.measure_text_ex(self.font, msg, size, 1).x if self.font else ui.text_width(msg, size)

    def _text(self, msg: str, x: float, y: float, size: float, color: pr.Color) -> None:
        if self.font:
            pr.draw_text_ex(self.font, msg, pr.Vector2(x, y), size, 1, color)
        else:
            ui.draw_text(msg, x, y, size, color)

    def _wrap(self, text: str, width: float) -> list[str]:
        """`text` cut into lines of at most `width` pixels, between words."""
        lines = [""]
        for word in text.split():
            longer = f"{lines[-1]} {word}".strip()
            if self._width(longer, TEXT_SIZE) <= width:
                lines[-1] = longer
            else:
                lines.append(word)
        return lines

    def _paper(self) -> None:
        """The torn page: binder teeth along the top, ruled lines, the bottom edge ripped, a strip of tape."""
        w, h = TUTORIAL_SIZE
        rng = random.Random(6)   # the same tear every time
        rip = 0.0
        for x in range(0, w, 6):
            rip = min(max(rip + rng.uniform(-7.0, 7.0), 0.0), TORN)
            pr.draw_rectangle(x, TOP, 6, h - TOP - int(rip), TUTORIAL_PAPER)
        for x in range(10, w - 30, 56):
            pr.draw_rectangle(x, 22, 26, TOP - 22, TUTORIAL_PAPER)
        pr.draw_rectangle(0, 14, w, 12, TUTORIAL_PAPER)
        for y in range(TOP + 150, h - TORN - 8, LINE):
            pr.draw_line_ex(pr.Vector2(30, y), pr.Vector2(w - 30, y), 3, TUTORIAL_RULE)
        pr.draw_rectangle_pro(pr.Rectangle(w * 0.5, 34, 300, 74), pr.Vector2(150, 37), -8.0, TUTORIAL_TAPE)

    def _render(self) -> None:
        w, _ = TUTORIAL_SIZE
        pr.begin_texture_mode(self.sheet)
        pr.clear_background(pr.Color(0, 0, 0, 0))   # around the paper: the wall
        self._paper()
        self._text(TUTORIAL_TITLE, (w - self._width(TUTORIAL_TITLE, TITLE_SIZE)) / 2, TOP + 26, TITLE_SIZE,
                   TUTORIAL_BLUE)
        y = TOP + 150 - LINE + 2
        for heading, text in TUTORIAL_TEXT:
            y += LINE
            self._text(heading, MARGIN, y - LINE + 4, TEXT_SIZE, TUTORIAL_RED)
            for line in self._wrap(text, w - 2 * MARGIN):
                self._text(line, MARGIN, y + 4, TEXT_SIZE, TUTORIAL_BLUE)
                y += LINE
        pr.end_texture_mode()

    def draw(self, lit: bool) -> None:
        # a render texture is stored upside down
        draw_quad(self.corners, self.sheet.texture.id, ((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)),
                  TUTORIAL_LIT if lit else TUTORIAL_DARK)

    def unload(self) -> None:
        pr.unload_render_texture(self.sheet)
        if self.font:
            pr.unload_font(self.font)
