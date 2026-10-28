"""Statistics: every saved run (records.py), from the main menu.

    StatsScreen().run(audio, menu.draw_background)   # until Zpět / Esc (True) or the window closes (False)

The list (newest first) shows each run's name, depth, time survived, what failed and when, with a summary on top
(how many runs, the deepest, the longest). The mouse wheel scrolls it; click a run to see its report (the same card
as on the death screen), Zpět or Esc goes back.
"""
from __future__ import annotations

from typing import Callable

import pyray as pr

from . import ui
from .audio import Audio
from .config import SCREEN_GREEN, SCREEN_H
from .records import Run, draw_record, format_time, load_runs

# In SCREEN_H-high pixels, scaled to the window
PANEL_W: float = 1200
PANEL_H: float = 760
ROW_H: float = 40
LIST_TOP: float = 190     # from the panel's top: the first row
LIST_ROWS: int = 12       # rows shown at once
TEXT: float = 24
# column: (header, x from the panel's left)
COLUMNS: tuple[tuple[str, float], ...] = (("Jméno", 40), ("Hloubka", 340), ("Přežitý čas", 480),
                                          ("Příčina", 680), ("Datum", 950))


class StatsScreen:
    def __init__(self) -> None:
        self.runs: list[Run] = load_runs()[::-1]   # newest first
        self.scroll: int = 0                        # the first row shown
        self.open: Run | None = None                # the run whose report is shown

    def run(self, audio: Audio, background: Callable[[], None]) -> bool:
        """Show it until Zpět / Esc (True) or the window closes (False). `background` draws the menu behind it."""
        while not pr.window_should_close():
            audio.update()
            pr.begin_drawing()
            background()
            back = self.draw()
            pr.end_drawing()
            if back:
                return True
        return False

    def draw(self) -> bool:
        """Draw it and handle the mouse and keys; True to leave."""
        w, h = pr.get_screen_width(), pr.get_screen_height()
        s = h / SCREEN_H
        esc = pr.is_key_pressed(pr.KeyboardKey.KEY_ESCAPE)
        if self.open is not None:   # one run's report
            pr.draw_rectangle(0, 0, w, h, pr.fade(pr.BLACK, 0.6))
            draw_record(self.open, w / 2, h / 2 - 190 * s, s)
            back = pr.Rectangle(w / 2 - 120 * s, h / 2 + 140 * s, 240 * s, 56 * s)
            if ui.button(back, "Zpět", 28 * s) or esc:
                self.open = None
            return False

        left, top = (w - PANEL_W * s) / 2, (h - PANEL_H * s) / 2
        pr.draw_rectangle_rec(pr.Rectangle(left, top, PANEL_W * s, PANEL_H * s), ui.PANEL)
        pr.draw_rectangle_lines_ex(pr.Rectangle(left, top, PANEL_W * s, PANEL_H * s), max(2.0, 3 * s), ui.DIM)
        ui.draw_centered("STATISTIKY", w / 2, top + 20 * s, 44 * s, ui.GREEN)
        ui.draw_centered(self._summary(), w / 2, top + 80 * s, 24 * s, pr.RAYWHITE)
        for header, x in COLUMNS:
            ui.draw_text(header, left + x * s, top + (LIST_TOP - 40) * s, TEXT * s, SCREEN_GREEN)

        self.scroll = min(max(self.scroll - int(pr.get_mouse_wheel_move()), 0), max(len(self.runs) - LIST_ROWS, 0))
        mouse = pr.get_mouse_position()
        for i, run in enumerate(self.runs[self.scroll:self.scroll + LIST_ROWS]):
            row = pr.Rectangle(left + 20 * s, top + (LIST_TOP + i * ROW_H) * s, (PANEL_W - 40) * s, ROW_H * s)
            if pr.check_collision_point_rec(mouse, row):
                pr.draw_rectangle_rec(row, pr.fade(ui.GREEN, 0.25))
                if pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
                    self.open = run
            values = (run.name, f"{run.depth:.0f} m", format_time(run.time), run.cause, run.date)
            for (_, x), value in zip(COLUMNS, values):
                ui.draw_text(value, left + x * s, row.y + (ROW_H - TEXT) / 2 * s, TEXT * s, pr.RAYWHITE)
        if not self.runs:
            ui.draw_centered("Zatím žádné záznamy. Uložte běh na konci mise.", w / 2, top + (LIST_TOP + 20) * s,
                             TEXT * s, ui.DIM)
        elif len(self.runs) > LIST_ROWS:
            shown = f"{self.scroll + 1}-{min(self.scroll + LIST_ROWS, len(self.runs))} z {len(self.runs)} (kolečko myši)"
            ui.draw_text(shown, left + 40 * s, top + (PANEL_H - 70) * s, 20 * s, ui.DIM)

        back = pr.Rectangle(left + (PANEL_W - 260) * s, top + (PANEL_H - 80) * s, 220 * s, 56 * s)
        return ui.button(back, "Zpět", 28 * s) or esc

    def _summary(self) -> str:
        if not self.runs:
            return "Počet misí: 0"
        deepest = max(self.runs, key=lambda r: r.depth)
        longest = max(self.runs, key=lambda r: r.time)
        return (f"Počet misí: {len(self.runs)}     Nejhlouběji: {deepest.depth:.0f} m ({deepest.name})     "
                f"Nejdéle: {format_time(longest.time)} ({longest.name})")
