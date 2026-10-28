"""Statistics: every saved run (records.py), from the main menu.

    StatsScreen().run(audio, menu.draw_background)   # until Zpět / Esc (True) or the window closes (False)

The list (newest first) shows each run's name, last reported depth, time survived, expected cause and when, with a
summary on top (how many runs, the deepest reported, the longest). The mouse wheel scrolls it; click a run to see
its report (the same card as on the death screen): Zpět or Esc goes back, Smazat záznam deletes it (after
"Opravdu smazat?").
"""
from __future__ import annotations

from typing import Callable

import pyray as pr

from . import ui
from .audio import Audio
from .config import SCREEN_GREEN, SCREEN_H
from .records import Run, delete_run, draw_record, format_time, load_runs

# In SCREEN_H-high pixels, scaled to the window
PANEL_W: float = 1200
PANEL_H: float = 760
ROW_H: float = 40
LIST_TOP: float = 190     # from the panel's top: the first row
LIST_ROWS: int = 12       # rows shown at once
TEXT: float = 22
# column: (header, x from the panel's left)
COLUMNS: tuple[tuple[str, float], ...] = (("Jméno", 40), ("Poslední hloubka", 290), ("Přežitý čas", 525),
                                          ("Předpokládaná příčina", 692), ("Datum", 980))


class StatsScreen:
    def __init__(self) -> None:
        self.runs: list[Run] = load_runs()[::-1]   # newest first
        self.scroll: int = 0                        # the first row shown
        self.open: Run | None = None                # the run whose report is shown
        self.confirm: bool = False                  # asking whether to delete it

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
            left = pr.Rectangle(w / 2 - 270 * s, h / 2 + 150 * s, 250 * s, 56 * s)
            right = pr.Rectangle(w / 2 + 20 * s, h / 2 + 150 * s, 250 * s, 56 * s)
            if self.confirm:
                ui.draw_centered("Opravdu smazat tento záznam?", w / 2, h / 2 + 110 * s, 26 * s, pr.RED)
                if ui.button(left, "Smazat", 28 * s):
                    delete_run(self.open)
                    self.runs.remove(self.open)
                    self.scroll = max(min(self.scroll, len(self.runs) - LIST_ROWS), 0)
                    self.open, self.confirm = None, False
                elif ui.button(right, "Zpět", 28 * s) or esc:
                    self.confirm = False
            else:
                if ui.button(left, "Smazat záznam", 28 * s):
                    self.confirm = True
                elif ui.button(right, "Zpět", 28 * s) or esc:
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
            values = (run.name, run.depth_text, format_time(run.time), run.cause_text, run.date)
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
        reported = [r for r in self.runs if r.depth is not None]
        deepest = max(reported, key=lambda r: r.depth) if reported else None
        longest = max(self.runs, key=lambda r: r.time)
        deep = f"{deepest.depth_text} ({deepest.name})" if deepest else "-"
        return (f"Počet misí: {len(self.runs)}     Nejhlouběji: {deep}     "
                f"Nejdéle: {format_time(longest.time)} ({longest.name})")
