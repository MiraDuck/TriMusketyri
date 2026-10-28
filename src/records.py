"""Records: the report of every run that was saved, kept in RUNS_FILE (JSON).

    run = Run(name, time, depth, cause, date)    # cause: what failed (a DEATH_TEXT_*)
    save_run(run)
    runs = load_runs()                           # oldest first
    last_name()                                  # the name of the last saved run, "" if none
    draw_record(run, cx, top, scale)             # the report card, as on the death screen and in the statistics
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime

import pyray as pr

from . import ui
from .config import RUNS_FILE, SCREEN_GREEN

CARD_W: float = 620   # the report card, in SCREEN_H-high pixels (drawn at `scale`)
CARD_H: float = 290


@dataclass
class Run:
    name: str
    time: float       # seconds survived
    depth: float      # metres reached
    cause: str        # what failed
    date: str = ""    # when it ended, "28.10.2026 14:05"

    @staticmethod
    def now() -> str:
        return datetime.now().strftime("%d.%m.%Y %H:%M")


def format_time(seconds: float) -> str:
    """12:05, or 1:02:05 past an hour."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def load_runs() -> list[Run]:
    if not RUNS_FILE.is_file():
        return []
    try:
        data = json.loads(RUNS_FILE.read_text(encoding="utf-8"))
        return [Run(**run) for run in data]
    except (ValueError, TypeError) as error:   # a broken file: say so, keep it, start a fresh list in memory
        print(f"RECORDS: can't read {RUNS_FILE.name}: {error}")
        return []


def save_run(run: Run) -> None:
    runs = load_runs() + [run]
    RUNS_FILE.write_text(json.dumps([asdict(r) for r in runs], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"RECORDS: saved run {len(runs)} ({ui.plain(run.name)}, {run.depth:.0f} m)")


def last_name() -> str:
    runs = load_runs()
    return runs[-1].name if runs else ""


def draw_record(run: Run, cx: float, top: float, scale: float, alpha: float = 1.0, caret: bool = False) -> None:
    """The report card centred on `cx` (screen pixels), its top at `top`. `caret`: the name is being typed."""
    w, h = CARD_W * scale, CARD_H * scale
    left = cx - w / 2
    pr.draw_rectangle_rec(pr.Rectangle(left, top, w, h), pr.fade(ui.PANEL, alpha))
    pr.draw_rectangle_lines_ex(pr.Rectangle(left, top, w, h), max(2.0, 3 * scale), pr.fade(ui.DIM, alpha))
    green, light = pr.fade(SCREEN_GREEN, alpha), pr.fade(pr.RAYWHITE, alpha)
    ui.draw_centered("ZÁZNAM MISE", cx, top + 18 * scale, 30 * scale, green)
    pr.draw_line_ex(pr.Vector2(left + 30 * scale, top + 60 * scale), pr.Vector2(left + w - 30 * scale, top + 60 * scale),
                    max(1.0, 2 * scale), pr.fade(ui.DIM, alpha))
    name = run.name + ("_" if caret and int(pr.get_time() * 2) % 2 == 0 else "")
    rows = [("Jméno", name), ("Přežitý čas", format_time(run.time)), ("Hloubka", f"{run.depth:.0f} m"),
            ("Příčina", run.cause), ("Datum", run.date)]
    for i, (label, value) in enumerate(rows):
        y = top + (78 + i * 40) * scale
        ui.draw_text(label + ":", left + 40 * scale, y, 26 * scale, green)
        ui.draw_text(value, left + 240 * scale, y, 26 * scale, light)
