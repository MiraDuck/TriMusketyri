"""Pause: Esc in the game stops it and asks whether to leave.

    choice = pause_menu()   # every frame while paused, after drawing the (frozen) game: draws itself
    # "leave": back to the main menu (the run is not saved), "resume": back into the game, None: still asking

Esc again also resumes (main.py).
"""
from __future__ import annotations

import pyray as pr

from . import ui
from .config import PAUSE_LEAVE, PAUSE_QUESTION, PAUSE_RESUME, SCREEN_H


def pause_menu() -> str | None:
    w, h = pr.get_screen_width(), pr.get_screen_height()
    s = h / SCREEN_H
    pr.draw_rectangle(0, 0, w, h, pr.fade(pr.BLACK, 0.7))
    for i, line in enumerate(PAUSE_QUESTION.split("\n")):
        ui.draw_centered(line, w / 2, h / 2 + (-140 + i * 50) * s, (40 if i == 0 else 28) * s,
                         pr.RAYWHITE if i == 0 else pr.GRAY)
    width, height, gap = 300 * s, 60 * s, 30 * s
    leave = pr.Rectangle(w / 2 - width - gap / 2, h / 2 + 10 * s, width, height)
    resume = pr.Rectangle(w / 2 + gap / 2, h / 2 + 10 * s, width, height)
    if ui.button(leave, PAUSE_LEAVE, 30 * s):
        return "leave"
    if ui.button(resume, PAUSE_RESUME, 30 * s):
        return "resume"
    return None
